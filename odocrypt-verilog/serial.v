// by teknohog, replaces virtual_wire by rs232

// Now using fpgaminer's uart code instead of fpga4fun's. Besides
// GPL3, the practical difference is that instead of TxD_busy we have
// its inverse tx_ready.

module serial_receive # (
   parameter baud_rate = 115_200,
   parameter comm_clk_frequency = 100_000_000 )
  ( clk, RxD, header, target, rx_done );
   input      clk;
   input      RxD;
   
   wire       RxD_data_ready;
   wire [7:0] RxD_data;


    // Timeout after 8 million clock at 100Mhz is 80ms, which should be
    // OK for all sensible clock speeds eg 20MHz is 400ms, 200MHz is 40ms
	parameter SERIAL_TIMEOUT = 24'h800000;

   uart_receiver #(.comm_clk_frequency(comm_clk_frequency), .baud_rate(baud_rate)) urx (.clk(clk), .uart_rx(RxD), .tx_new_byte(RxD_data_ready), .tx_byte(RxD_data));
   
   
   output [607:0] header;
   output [95:0] target;
   
   output reg rx_done;
   
   reg [703:0] input_buffer;
   reg [703:0] input_copy;
   reg [6:0]   demux_state;
   reg [23:0]  timer;
   
   assign header = input_copy[703:96];
   assign target = input_copy[95:0];
   
   always @(posedge clk)
     case (demux_state)
       7'b1011000: begin    	// 88 bytes loaded
		 rx_done <= 1'b1;
	     input_copy <= input_buffer;
	     demux_state <= 1'b0;
	   end
       
       default: begin
         rx_done <= 1'b0;
	     if(RxD_data_ready)
	       begin
	         input_buffer <= input_buffer << 8;
	         input_buffer[7:0] <= RxD_data;
             demux_state <= demux_state + 1'b1;
	         timer <= 1'b0;
	       end else begin
	         timer <= timer + 1;
	         if (timer == SERIAL_TIMEOUT)
	           demux_state <= 1'b0;
	         end
       end // default
     endcase // case (demux_state)
   
endmodule // serial_receive

module serial_transmit # (
   parameter baud_rate = 115_200,
   parameter comm_clk_frequency = 100_000_000 )
  (clk, TxD, busy, send, word);

   wire TxD_start;
   wire TxD_ready;
   
   reg [7:0]  out_byte = 0;
   reg        serial_start = 0;
   reg [3:0]  mux_state = 4'b0000;

   assign TxD_start = serial_start;

   input      clk;
   output     TxD;
   
   input [31:0] word;
   input 	send;
   output reg	busy;
   
   reg [31:0] 	word_copy = 0;

   always @(posedge clk) begin
      case (mux_state)
         4'b0000: begin
            if (send) begin
               word_copy <= word;
               if (TxD_ready) mux_state <= mux_state + 1;
            end
         end
         4'b0001: begin
            busy <= 1;
            out_byte <= word_copy[31:24];
            serial_start <= 1;
            mux_state <= mux_state + 1;
         end
         4'b0010: begin
            serial_start <= 0;
            if (TxD_ready) mux_state <= mux_state + 1;
         end
         4'b0011: begin
            out_byte <= word_copy[23:16];
            serial_start <= 1;
            mux_state <= mux_state + 1;
         end
         4'b0100: begin
            serial_start <= 0;
            if (TxD_ready) mux_state <= mux_state + 1;
         end
         4'b0101: begin
            out_byte <= word_copy[15:8];
            serial_start <= 1;
            mux_state <= mux_state + 1;
         end
         4'b0110: begin
            serial_start <= 0;
            if (TxD_ready) mux_state <= mux_state + 1;
         end
         4'b0111: begin
            out_byte <= word_copy[7:0];
            serial_start <= 1;
            mux_state <= mux_state + 1;
         end
         4'b1000: begin
            serial_start <= 0;
            if (TxD_ready) mux_state <= mux_state + 1;
         end
         4'b1001: begin
            out_byte <= 8'b00001010; //newline
            serial_start <= 1;
            mux_state <= mux_state + 1;
         end
         4'b1010: begin
            serial_start <= 0;
            if (TxD_ready) mux_state <= mux_state + 1;
         end
         4'b1011: begin
            busy <= 0;
            mux_state <= 0;
         end
      endcase
   end
   
   uart_transmitter #(.comm_clk_frequency(comm_clk_frequency), .baud_rate(baud_rate)) utx (.clk(clk), .uart_tx(TxD), .rx_new_byte(TxD_start), .rx_byte(out_byte), .tx_ready(TxD_ready));

endmodule // serial_send