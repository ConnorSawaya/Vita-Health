
#modules
import streamlit as st
import os
try:
    from pyzbar.pyzbar import decode
    PYZBAR_OK = True
except Exception:
    decode = None
    PYZBAR_OK = False
try:
    import cv2
    CV2_OK = True
except Exception:
    cv2 = None
    CV2_OK = False
from ai import add_scan_to_history, ai_analysis, handle_follow_up, MOCK_ANALYSIS
SCANNER_OK = PYZBAR_OK and CV2_OK
if "stuff" not in st.session_state:
    st.session_state.stuff = 0
if "scan_history" not in st.session_state:
    st.session_state.scan_history = []

def scan_frame(frame):
    if not SCANNER_OK:
        return []
    barcodes = decode(frame)
    results = []
    for barcode in barcodes:
        barcode_data = barcode.data.decode("utf-8")
        barcode_type = barcode.type
        results.append((barcode_data, barcode_type))
    return results
def main():
    # --- State Management ---
    if "scanning" not in st.session_state:
        st.session_state.scanning = False
    if "camera_choice" not in st.session_state:
        st.session_state.camera_choice = 0

    # --- UI Stuff ---
    st.title("Vita Health")
    if not SCANNER_OK:
        st.warning("Scanner libraries (pyzbar/opencv) unavailable — running in DEMO mode. Use the demo button below; camera scanning needs a full desktop install.")
    if not os.getenv("OPENROUTER_API_KEY"):
        st.info("OFFLINE/MOCK mode: no OPENROUTER_API_KEY. Analyses use built-in sample data. Add the key in .env for live AI.")
    if st.button("Load demo product (offline)"):
        with st.spinner("Loading demo analysis..."):
            add_scan_to_history(
                st.session_state.scan_history,
                "3017620422003",
                "Demo: Nutella Hazelnut Spread",
                MOCK_ANALYSIS,
            )
        st.rerun()

    # Placeholder for video feed or results
    display_slot = st.empty()

    # --- Camera Loop & Scanning Logic ---
    if st.session_state.scanning:
        if not SCANNER_OK:
            st.error("Camera scanning unavailable in this install (missing pyzbar/opencv). Use the demo button instead.")
            st.session_state.scanning = False
            st.rerun()
        display_slot.info("Point camera at a barcode...")
        cap = cv2.VideoCapture(st.session_state.camera_choice)
        if not cap.isOpened():
            st.error("Failed to open camera. Check permissions.")
            st.session_state.scanning = False
            st.rerun()

        while st.session_state.scanning:
            ret, cam_frame = cap.read()
            if not ret:
                st.warning("Failed to grab frame.")
                break

            frame_rgb = cv2.cvtColor(cam_frame, cv2.COLOR_BGR2RGB)
            display_slot.image(frame_rgb, channels="RGB")

            results = scan_frame(cam_frame)
            if any(typ == "EAN13" for _, typ in results):
                data, _ = next((d, t) for d, t in results if t == "EAN13")
                ai_analysis(str(data), st.session_state.scan_history)
                st.session_state.scanning = False
                break
        
        cap.release()
        cv2.destroyAllWindows()
        st.rerun()
    else:
        if st.session_state.scan_history:
            with display_slot.container():
                st.subheader("Scan History")
                for item in st.session_state.scan_history:
                    # Use .get() to safely access keys that might be missing in old records
                    product_name = item.get('product_name', 'Unknown Product')
                    timestamp = item.get('timestamp', 'No date')
                    ai_result = item.get('ai_result', 'No analysis available.')

                    st.markdown(f"**{product_name}** ({timestamp})")
                    st.markdown(ai_result)
                    
                    # Display chat log for each item
                    for chat in item.get('chat_log', []):
                        with st.chat_message("user"):
                            st.write(chat["user"])
                        with st.chat_message("assistant"):
                            st.write(chat["ai"])
                    st.divider()
        else:
            display_slot.info("Scan an item to see the analysis here.")
        # --- Control Panel ---
        st.divider()
        use_front_camera = st.toggle("Use Front/Back Camera")
        st.session_state.camera_choice = 1 if use_front_camera else 0
        
        if st.button("Start Scanner"):
            st.session_state.scanning = True
            st.rerun()
        
        # Capture and handle chat input
        if prompt := st.chat_input("Ask a follow-up about the last scan..."):
            previous_chat_count = (
                len(st.session_state.scan_history[0].get("chat_log", []))
                if st.session_state.scan_history
                else 0
            )
            message = handle_follow_up(prompt, st.session_state.scan_history)
            current_chat_count = (
                len(st.session_state.scan_history[0].get("chat_log", []))
                if st.session_state.scan_history
                else 0
            )
            st.session_state.follow_up_notice = (
                message if current_chat_count == previous_chat_count else ""
            )
            st.rerun()

        if st.session_state.get("follow_up_notice"):
            st.warning(st.session_state.follow_up_notice)

if __name__ == "__main__":
    main()
