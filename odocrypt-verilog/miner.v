`timescale 1ns / 1ps

`define  THROUGHPUT 21

module cmp_256(clk, in, read, target_reduced, out, write);
    input clk;
    input [255:0] in;
    input read;
    input [95:0] target_reduced;
    output reg out;
    output reg write;
    
    reg [15:0] greater, less;
    reg progress;
    initial progress = 0;
    initial write = 0;
    
    wire [255:0] target;
    assign target = {16'b0, target_reduced, 144'b0};
    
    genvar i;
    generate
    for (i = 0; i < 16; i = i+1)
    begin : loop
        always @(posedge clk)
        begin
            greater[i] <= (in[16*i+15:16*i] > target[16*i+15:16*i]);
            less[i] <= (in[16*i+15:16*i] < target[16*i+15:16*i]);
        end
    end
    endgenerate
    
    always @(posedge clk)
    begin
        out <= (greater < less);
        progress <= read;
        write <= progress;
    end
endmodule

module odo_keccak(clk, in, read, target_reduced, out, write);
    input clk;
    input [639:0] in;
    input read;
    input [95:0] target_reduced;
    output out;
    output write;

    wire [639:0] midstate;
    wire midread;
    wire [255:0] pow_hash;
    wire has_hash;
    
    odo_encrypt crypt(clk, in, read, midstate, midread);
    keccak_hasher #(640, `THROUGHPUT) hash(clk, midstate, midread, pow_hash, has_hash);
    cmp_256 compare(clk, pow_hash, has_hash, target_reduced, out, write);
endmodule

module miner(clk, header, target_reduced, nonce, valid, nonce_vio, rst);
    parameter INONCE = 12; // for testing

    input clk;
    input [607:0] header;
    input [95:0] target_reduced;
    input rst;
    output reg [31:0] nonce;
    output valid;
    output [31:0] nonce_vio;
    
    reg [31:0] nonce_in;
    reg [31:0] nonce_out;
    initial nonce_in = INONCE;
    initial nonce_out = INONCE;
    
    reg [6:0] counter;
    reg advance;
    initial counter = `THROUGHPUT-1;
    initial advance = 0;
    
    wire res;
    wire has_res;
    
    assign nonce_vio = nonce_in;
    assign valid = res;
    
    odo_keccak worker(clk, {nonce_in, header}, advance, target_reduced, res, has_res);
    
    always @(posedge clk)
    begin
        if (counter == `THROUGHPUT-1) begin
            counter <= 0;
            advance <= 1;
        end else begin
            counter <= counter + 1;
            advance <= 0;
        end
        
        if (advance) begin
            nonce_in <= nonce_in + 13;
        end else if (rst) begin
            nonce_in <= 32'b1100;
        end
        
        /*if (has_res) begin
            if (res) nonce <= nonce_out;
            nonce_out <= nonce_out + 1;
        end*/
    end
endmodule

module miner_top(hash_clk, uart_clk, rx, tx, rx_done_led, res_led);
	input hash_clk;
	input uart_clk;
	input rx;
	output tx;
	output rx_done_led;
	output res_led;
	
	
	wire [31:0] nonce_hash;
	wire [607:0] header;
	wire [95:0] target_reduced;

	wire [31:0] nonce;
	
	parameter baud_rate = 115_200;
    parameter comm_clk_frequency = 170_000_000;

	wire valid;
    wire busy;
    wire rx_done;
    wire send_sig;
    
    assign rx_done_led = rx_done;
    assign res_led = valid;
    
    assign send_sig = valid && ~busy;
    assign send_wire = (send_sig == 1)? 1 : 0;
    assign rst = rx_done;
    
    serial_receive #(.comm_clk_frequency(comm_clk_frequency), .baud_rate(baud_rate)) rxd (.clk(uart_clk), .RxD(rx), .header(header), .target(target_reduced), .rx_done(rx_done));
    serial_transmit #(.comm_clk_frequency(comm_clk_frequency), .baud_rate(baud_rate)) txd (.clk(uart_clk), .TxD(tx), .busy(busy), .send(send_wire), .word(nonce_hash));
	
	miner miner (hash_clk, header, target_reduced, nonce, valid, nonce_hash, rst);
	
endmodule
	
