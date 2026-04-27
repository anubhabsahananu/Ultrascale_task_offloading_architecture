Pga 

from flask import Flask, request, send_file, make_response
from pynq import Overlay, allocate
import numpy as np
import threading, time, io, math
from PIL import Image

# --- Initialization ---
ol = Overlay("four_engine.bit")
hw_lock = threading.Lock()

# --- Hardware Resource Table ---
resource_table = {
    "ai":      threading.Lock(),
    "crypto":  threading.Lock(),
    "image":   threading.Lock(),
    "matmul":  threading.Lock()
}

# --- High-Volume Stress Buffers ---
# AI/Crypto: 10,000 elements | MatMul: 32x32 (1024) | Image: 64x64
bufs = {
    "ai":     (allocate(shape=(10000,), dtype='f4'), allocate(shape=(10000,), dtype='f4')),
    "crypto": (allocate(shape=(10000,), dtype='i4'), allocate(shape=(10000,), dtype='i4')),
    "image":  (allocate(shape=(64, 64, 4), dtype=np.uint8), allocate(shape=(64, 64, 4), dtype=np.uint8)),
    "matmul": (allocate(shape=(2048,), dtype='f4'), allocate(shape=(1024,), dtype='f4'))
}

def ensure_dma(dma):
    """Restart DMA if it has entered a halted state."""
    if not dma.sendchannel.running or not dma.recvchannel.running:
        dma.register_map.MM2S_DMACR.Reset = 1
        dma.register_map.S2MM_DMACR.Reset = 1
        while dma.register_map.MM2S_DMACR.Reset == 1: time.sleep(0.001)
        dma.register_map.MM2S_DMACR.RS = 1
        dma.register_map.S2MM_DMACR.RS = 1

# --- Flask App ---
app = Flask(__name__)

def create_hw_response(result_bytes, arrival, start_ex, end_ex, is_image=False):
    """Calculates timings and packages the response."""
    wait_ms = (start_ex - arrival) * 1000
    exec_ms = (end_ex - start_ex) * 1000
    
    if is_image:
        resp = make_response(send_file(result_bytes, mimetype="image/png"))
    else:
        resp = make_response(result_bytes)
    
    resp.headers["Wait-Time-ms"] = f"{wait_ms:.3f}"
    resp.headers["Exec-Time-ms"] = f"{exec_ms:.3f}"
    return resp

@app.route("/process_ai", methods=["POST"])
def api_ai():
    arrival = time.perf_counter()
    data = np.frombuffer(request.data, dtype='f4')
    
    with resource_table["ai"]:
        start_ex = time.perf_counter()
        ensure_dma(ol.axi_dma_0)
        
        bufs["ai"][0][:len(data)] = data
        
        # Arm both channels
        ol.axi_dma_0.sendchannel.transfer(bufs["ai"][0])
        ol.axi_dma_0.recvchannel.transfer(bufs["ai"][1])
        
        ol.ai_relu_engine_0.write(0x10, len(data))
        ol.ai_relu_engine_0.write(0x00, 0x01)
        
        # CRITICAL: Wait for BOTH to be idle before releasing the lock
        ol.axi_dma_0.sendchannel.wait()
        ol.axi_dma_0.recvchannel.wait()
        
        res = bufs["ai"][1][:len(data)].tobytes()
        end_ex = time.perf_counter()
        
    return create_hw_response(res, arrival, start_ex, end_ex)

@app.route("/process_crypto", methods=["POST"])
def api_crypto():
    arrival = time.perf_counter()
    data = np.frombuffer(request.data, dtype='i4')
    with resource_table["crypto"]:
        start_ex = time.perf_counter()
        ensure_dma(ol.axi_dma_1)
        bufs["crypto"][0][:len(data)] = data
        ol.axi_dma_1.sendchannel.transfer(bufs["crypto"][0])
        ol.axi_dma_1.recvchannel.transfer(bufs["crypto"][1])
        ol.crypto_engine_0.write(0x10, 0x12345678)
        ol.crypto_engine_0.write(0x18, len(data))
        ol.crypto_engine_0.write(0x00, 0x01)
        ol.axi_dma_1.recvchannel.wait()
        res = bufs["crypto"][1][:len(data)].tobytes()
        end_ex = time.perf_counter()
    return create_hw_response(res, arrival, start_ex, end_ex)

@app.route("/process_image", methods=["POST"])
def api_image():
    arrival = time.perf_counter()
    file = request.files['image']
    img = Image.open(file.stream).convert("RGBA").resize((64,64))
    img_np = np.asarray(img, dtype=np.uint8)
    with resource_table["image"]:
        start_ex = time.perf_counter()
        ensure_dma(ol.axi_dma_2)
        bufs["image"][0][:] = img_np
        ol.axi_dma_2.sendchannel.transfer(bufs["image"][0])
        ol.axi_dma_2.recvchannel.transfer(bufs["image"][1])
        ol.image_filter_engine_0.write(0x10, 64)
        ol.image_filter_engine_0.write(0x18, 64)
        ol.image_filter_engine_0.write(0x00, 0x01)
        ol.axi_dma_2.recvchannel.wait()
        res_np = bufs["image"][1].copy()
        end_ex = time.perf_counter()
    
    out_img = Image.fromarray(res_np, mode="RGBA")
    buf = io.BytesIO(); out_img.save(buf, format="PNG"); buf.seek(0)
    return create_hw_response(buf, arrival, start_ex, end_ex, is_image=True)

@app.route("/process_matmul", methods=["POST"])
def api_matmul():
    arrival = time.perf_counter()
#     status = ol.matmul_engine_0.read(0x00)
#     print(f"IP Status Register: {hex(status)}")
    data = np.frombuffer(request.data, dtype='f4')
    with resource_table["matmul"]:
        start_ex = time.perf_counter()
        ensure_dma(ol.axi_dma_3)
        bufs["matmul"][0][:len(data)] = data
        
        ol.axi_dma_3.recvchannel.transfer(bufs["matmul"][1])
        ol.matmul_engine_0.write(0x00, 0x01)
        ol.axi_dma_3.sendchannel.transfer(bufs["matmul"][0])
        
        ol.axi_dma_3.recvchannel.wait()
        res = bufs["matmul"][1][:1024].tobytes() # Output is half of input size
        end_ex = time.perf_counter()
    return create_hw_response(res, arrival, start_ex, end_ex)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
