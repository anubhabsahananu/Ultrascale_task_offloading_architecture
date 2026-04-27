#include "hls_stream.h"
#include "ap_axi_sdata.h"

typedef hls::axis<int, 0, 0, 0> pkt;

void crypto_engine(
    hls::stream<pkt> &in_data, 
    hls::stream<pkt> &out_data, 
    int key, 
    int size,
    bool mode // 0: Encrypt, 1: Decrypt
) {
    // Port Pragmas
    #pragma HLS INTERFACE axis port=in_data
    #pragma HLS INTERFACE axis port=out_data
    #pragma HLS INTERFACE s_axilite port=key bundle=control
    #pragma HLS INTERFACE s_axilite port=size bundle=control
    #pragma HLS INTERFACE s_axilite port=mode bundle=control
    #pragma HLS INTERFACE s_axilite port=return bundle=control

    for (int i = 0; i < size; i++) {
        #pragma HLS PIPELINE II=1
        #pragma HLS LOOP_TRIPCOUNT min=1 max=1024
        
        pkt curr_pkt = in_data.read();
        
        // Simple Stream Cipher Logic (XOR)
        // In a real M.Tech project, you could replace this with AES or DES logic
        int processed_val = curr_pkt.data ^ key;

        curr_pkt.data = processed_val;
        out_data.write(curr_pkt);
    }
}
