#!/usr/bin/env python3
"""
Compatibility entrypoint for Streamlit Cloud - thin wrapper delegating to marketing_analytics_hub.main
"""

from marketing_analytics_hub import main as hub_main


if __name__ == "__main__":
    hub_main()