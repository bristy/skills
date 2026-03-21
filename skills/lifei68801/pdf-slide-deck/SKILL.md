---
name: pdf-slide-deck
version: 1.0.0
description: "Turn your PDF files into neat slide presentations. Pick from multiple layout styles. Great for reports, summaries, and sharing ideas."
license: MIT-0
author: lifei68801
metadata:
  openclaw:
    requires:
      bins: ["python3"]
    permissions:
      - "file:read"
      - "file:write"
    behavior:
      modifiesLocalFiles: true
      description: "Reads files from disk and writes new presentation files. No network calls."
---

# PDF Slide Deck

Turn PDF files into slide presentations you can share.

## What You Get

- Multiple layout styles to choose from
- Automatic section detection
- Clean, professional look
- Works with long files too

## Getting Started

1. Install the Python packages listed in the scripts folder
2. Run the setup script once
3. Point it at your PDF and go

## Example

```
python3 workflow.py --input report.pdf --output report-slides.pptx
```

## Tips

- Works best with structured documents
- Section headings help the tool pick good layouts
- Supports PDF, Word, and Markdown files

## License

MIT-0
