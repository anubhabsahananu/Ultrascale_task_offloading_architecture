#include "hls_stream.h"
#include "ap_axi_sdata.h"

// Define a 32-bit pixel structure (4 bytes)
struct pixel {
    unsigned char r;
    unsigned char g;
    unsigned char b;
    unsigned char a; // Padding byte to ensure 32-bit alignment
};

// Use the standard AXI-Stream sideband structure
typedef hls::axis<pixel, 0, 0, 0> img_pkt;

void image_filter_engine(
    hls::stream<img_pkt> &in_img, 
    hls::stream<img_pkt> &out_img, 
    int width, 
    int height
) {
    // Interface Pragmas
    #pragma HLS INTERFACE axis port=in_img
    #pragma HLS INTERFACE axis port=out_img
    #pragma HLS INTERFACE s_axilite port=width bundle=control
    #pragma HLS INTERFACE s_axilite port=height bundle=control
    #pragma HLS INTERFACE s_axilite port=return bundle=control

    int total_pixels = width * height;

    // Pipeline with Initiation Interval (II) of 1 for max throughput
    for (int i = 0; i < total_pixels; i++) {
        #pragma HLS PIPELINE II=1
        
        img_pkt curr_pixel = in_img.read();
        
        // Grayscale conversion: Y = 0.299R + 0.587G + 0.114B
        // Efficient integer approximation for FPGA
        unsigned char gray = (curr_pixel.data.r * 77 + 
                              curr_pixel.data.g * 150 + 
                              curr_pixel.data.b * 29) >> 8;

        // Assign gray value to all color channels
        curr_pixel.data.r = gray;
        curr_pixel.data.g = gray;
        curr_pixel.data.b = gray;
        // Alpha remains unchanged (usually 255 for opaque)
        curr_pixel.data.a = curr_pixel.data.a; 

        out_img.write(curr_pixel);
    }
}
