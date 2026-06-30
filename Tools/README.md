# EcoSIM Tools

This directory contains various Python tools that support the EcoSIM biogeochemical modeling framework. These tools assist with data processing, visualization, and integration with the EcoSIM model.

## Available Tools

### vision_tool.py
A tool for querying vision models (specifically Qwen2.5-VL) to extract information from images.

**Purpose:**
- Extract text or information from images using local vision models
- Intended for processing images related to soil profiles, climate data visualizations, or other scientific imagery

**Usage:**
```bash
python vision_tool.py path/to/image.png "What text is in this image?"
```

**Requirements:**
- Local vision model running at `http://localhost:11434/api/chat`
- Python packages: requests, base64, sys

**Note:** This tool requires a local Ollama instance running with the Qwen2.5-VL model to function properly.

## Contributing

When adding new tools to this directory:
1. Document the tool's purpose and usage
2. Include necessary installation or setup instructions
3. Follow the existing code style and conventions
4. Ensure tools are compatible with the EcoSIM framework

## License

This directory's contents are part of the EcoSIM research framework and are subject to the project's licensing terms.