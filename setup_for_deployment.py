#!/usr/bin/env python3
"""
Setup script for World Flags Application deployment
"""

import os
import json
from pathlib import Path
from src.downloader import FlagDownloader
from src.analyzer import FlagAnalyzer

def setup_deployment():
    """Initialize the application for deployment"""
    
    print("🚀 Setting up World Flags Application for deployment...")
    
    # Create necessary directories
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    flags_dir = data_dir / "flags"
    flags_dir.mkdir(exist_ok=True)
    
    # Download and process flags if not already done
    countries_file = data_dir / "countries.json"
    features_file = data_dir / "flag_features.json"
    
    try:
        # Initialize downloader
        downloader = FlagDownloader(data_dir)
        
        # Download countries data if not exists
        if not countries_file.exists():
            print("📥 Downloading countries data...")
            downloader.download_countries_data()
        
        # Download some sample flags for demo
        print("🏳️ Downloading sample flags...")
        sample_countries = [
            'us', 'gb', 'fr', 'de', 'it', 'es', 'ca', 'jp', 'au', 'br',
            'cn', 'in', 'ru', 'za', 'eg', 'ng', 'mx', 'ar', 'cl', 'kr'
        ]
        
        for country in sample_countries:
            try:
                downloader.download_flag(country)
            except Exception as e:
                print(f"⚠️  Warning: Could not download flag for {country}: {e}")
        
        # Analyze flags if not already done
        if not features_file.exists():
            print("🔍 Analyzing flags...")
            analyzer = FlagAnalyzer(data_dir)
            analyzer.analyze_all_flags()
        
        print("✅ Setup complete! Application ready for deployment.")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    setup_deployment() 