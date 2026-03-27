#!/usr/bin/env python3
import json
import sys
import os
import requests
import base64
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright

# Koppen mapping per SKILL.md
koppenDict = {
    "Af": 11, "Am": 12, "As": 13, "Aw": 14, "BWk": 21, "BWh": 22, "BSk": 26, "BSh": 27,
    "Cfa": 31, "Cfb": 32, "Cfc": 33, "Csa": 34, "Csb": 35, "Csc": 36, "Cwa": 37, "Cwb": 38, "Cwc": 39,
    "Dfa": 41, "Dfb": 42, "Dfc": 43, "Dfd": 44, "Dsa": 45, "Dsb": 46, "Dsc": 47, "Dsd": 48,
    "Dwa": 49, "Dwb": 50, "Dwc": 51, "Dwd": 52, "ET": 61, "EF": 62
}

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def query_vision_model(image_path: str, site_id: str):
    """Integrates your vision_tool.py logic to query local Qwen via Ollama."""
    base64_image = encode_image(image_path)
    
    # Prompt optimized for structured JSON extraction from the AmeriFlux UI
    prompt = (
        f"Analyze this screenshot of AmeriFlux site {site_id}. "
        "Extract the following values and return them in a strict JSON format: "
        "latitude, longitude, elevation, MAT, climate_code (e.g., BSk, Af), igbp_type (e.g., GRA, ENF, DBF). "
        "Only return the JSON object."
    )

    payload = {
        "model": "qwen2.5vl:7b",
        "messages": [{"role": "user", "content": prompt, "images": [base64_image]}],
        "stream": False,
    }

    try:
        response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=300)
        response.raise_for_status()
        content = response.json()["message"]["content"]
        
        # Clean the output in case the model adds markdown formatting
        json_str = content.replace("```json", "").replace("```", "").strip()
        return json.loads(json_str)
    except Exception as e:
        print(f"Vision tool failed: {e}")
        return None

def map_vegetation(igbp: str) -> int:
    """Logic per SKILL.md: ENF -> 11, DBF -> 10."""
    igbp = str(igbp).upper()
    if "ENF" in igbp: return 11
    if "DBF" in igbp: return 10
    return 10 # Default fallback

def run_vision_rag_flow(site_id: str, output_dir: str = "result"):
    url = f"https://ameriflux.lbl.gov/sites/siteinfo/{site_id}"
    img_path = f"{output_dir}/images/{site_id}_screenshot.png"
    
    with sync_playwright() as p:
        try:
            print(f"Step 1: Capturing screenshot for {site_id}...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 1600})
            page.goto(url, wait_until="networkidle")
            # Scroll to ensure metadata is in frame if necessary
            page.screenshot(path=img_path)
            browser.close()
            
            print(f"Step 2: Processing image with Qwen2.5-VL...")
            raw_data = query_vision_model(img_path, site_id)
            
            if raw_data:
                # Step 3: Map to JSON Variables per SKILL.md
                final_json = {
                    "site_name": site_id,
                    "ALATG": float(raw_data.get("latitude", 0.0)),
                    "ALONG": float(raw_data.get("longitude", 0.0)),
                    "ALTIG": float(raw_data.get("elevation", 0.0)),
                    "ATCAG": float(raw_data.get("MAT", 0.0)),
                    "IETYPG": koppenDict.get(raw_data.get("climate_code"), 0),
                    "IXTYP1": map_vegetation(raw_data.get("igbp_type", ""))
                }
                
                output_file = f"{output_dir}/{site_id}_ecosim_site.json"
                with open(output_file, "w") as f:
                    json.dump(final_json, f, indent=4)
                print(f"Successfully created {output_file}")
                print(json.dumps(final_json, indent=4))
            
        except Exception as e:            
            print(f"Error during vision RAG flow: {e}")
            print("Ensure that Ollama is running with the Qwen2.5-VL model and that Playwright dependencies are installed.")
            print(f"check image for {site_id} at {img_path}.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_vision_rag_flow(sys.argv[1])
    else:
        print("Usage: python extract_ameriflux_site_data.py <SITE_ID>")