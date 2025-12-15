
#modules
from pyzbar.pyzbar import decode
import streamlit as st
import cv2
import os
import json
import requests
from ai import ai_analysis, handle_follow_up
if "stuff" not in st.session_state:
    st.session_state.stuff = 0

def scan_frame(frame):
    barcodes = decode(frame)
    results = []
    for barcode in barcodes:
        barcode_data = barcode.data.decode("utf-8")
        barcode_type = barcode.type
        results.append((barcode_data, barcode_type))
    return results
HISTORY_FILE = "ai_analysis_history.json"
def load_scan_history():
    """Load history from the JSON file."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                # Load and reverse the list so newest is first
                return list(reversed(json.load(f)))
            except (json.JSONDecodeError, IndexError):
                return []
    return []
def main():
    # --- State Management ---
    if "scanning" not in st.session_state:
        st.session_state.scanning = False
    if "camera_choice" not in st.session_state:
        st.session_state.camera_choice = 0

    # Load history from file on each run
    st.session_state.scan_history = load_scan_history()

    # --- UI Stuff ---
    st.title("Vita Health")

    # Placeholder for video feed or results
    display_slot = st.empty()

    # --- Camera Loop & Scanning Logic ---
    if st.session_state.scanning:
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
                ai_analysis(str(data)) # This saves to file
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
            handle_follow_up(prompt)
            st.rerun()

if __name__ == "__main__":
    main()