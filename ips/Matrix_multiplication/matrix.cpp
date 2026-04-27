#include "hls_stream.h"
#include "ap_axi_sdata.h"

#define SIZE 32

typedef hls::axis<float, 0, 0, 0> pkt;

void matmul_engine(hls::stream<pkt> &in_data, hls::stream<pkt> &out_data) {
    // Port Pragmas
    #pragma HLS INTERFACE axis port=in_data
    #pragma HLS INTERFACE axis port=out_data
    #pragma HLS INTERFACE s_axilite port=return bundle=control

    float A[SIZE][SIZE];
    float B[SIZE][SIZE];
    float C[SIZE][SIZE];

    // Local buffers partitioning to allow parallel access
    #pragma HLS ARRAY_PARTITION variable=A cyclic factor=32 dim=2
    #pragma HLS ARRAY_PARTITION variable=B cyclic factor=32 dim=1

    // 1. Read Matrix A from Stream
    for (int i = 0; i < SIZE; i++) {
        for (int j = 0; j < SIZE; j++) {
            #pragma HLS PIPELINE II=1
            pkt curr = in_data.read();
            A[i][j] = curr.data;
        }
    }

    // 2. Read Matrix B from Stream
    for (int i = 0; i < SIZE; i++) {
        for (int j = 0; j < SIZE; j++) {
            #pragma HLS PIPELINE II=1
            pkt curr = in_data.read();
            B[i][j] = curr.data;
        }
    }

    // 3. Matrix Multiplication Logic
    // Complexity O(N^3), but unrolling makes it much faster
    for (int i = 0; i < SIZE; i++) {
        for (int j = 0; j < SIZE; j++) {
            #pragma HLS PIPELINE II=1
            float sum = 0;
            for (int k = 0; k < SIZE; k++) {
                // This inner loop is unrolled by the compiler due to PIPELINE in the outer loop
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }

    // 4. Write Matrix C back to Stream
    for (int i = 0; i < SIZE; i++) {
        for (int j = 0; j < SIZE; j++) {
            #pragma HLS PIPELINE II=1
            pkt curr;
            curr.data = C[i][j];
            curr.keep = -1;
            curr.last = (i == SIZE - 1 && j == SIZE - 1);
            out_data.write(curr);
        }
    }
}
