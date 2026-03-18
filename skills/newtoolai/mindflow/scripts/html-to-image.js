#!/usr/bin/env node

/**
 * HTML to Image Converter
 * Converts HTML files to images (PNG, JPEG) using node-html-to-image
 *
 * Supported formats: PNG, JPEG
 * Note: WebP and SVG are not directly supported by node-html-to-image
 *       (WebP requires puppeteer with specific flags, SVG output uses html-to-image library)
 */

import nodeHtmlToImage from 'node-html-to-image';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Supported image types
const SUPPORTED_TYPES = ['png', 'jpeg', 'jpg'];

// Default settings
const DEFAULT_QUALITY = 80;
const DEFAULT_WIDTH = 2560;
const DEFAULT_HEIGHT = 1664;
const DEFAULT_TIMEOUT = 120000; // 120 seconds for complex pages

/**
 * Display help information
 */
function showHelp() {
  console.log(`
HTML to Image Converter
=======================

Converts HTML files to images (PNG, JPEG) using node-html-to-image with puppeteer.

Usage:
  node html-to-image.js [options] <input-html> <output-image>

Arguments:
  input-html                  Path to input HTML file
  output-image                Path to output image (optional, defaults to input name with .png)

Options:
  -t, --type <format>         Output image format: png, jpeg, jpg (default: png)
  --width <pixels>        Image width in pixels (default: 1920)
  --height <pixels>       Image height in pixels (default: 1080)
  -q, --quality <0-100>       Image quality for JPEG (0-100, default: 80)
  --timeout <ms>              Timeout for rendering in milliseconds (default: 120000)
  --help                      Display this help message
  --version                   Display version information

Examples:
  # Convert to JPEG with custom quality
  node html-to-image.js input.html output.jpg

  # Convert with custom resolution
  node html-to-image.js input.html --width 3840 --height 2160 output.jpg

  # Full example
  node html-to-image.js input.html -t png --width 1920 --height 1080 -q 80 output.jpg

Notes:
  - PNG does not support quality parameter (lossless format)
  - JPEG quality ranges from 0 (lowest) to 100 (highest)
  - Resolution is set via CSS on the body element
  - The HTML should include proper styling for best results
`);
}

/**
 * Display version information
 */
function showVersion() {
  console.log('1.0.0');
}

/**
 * Parse command line arguments
 */
function parseArgs(args) {
  const options = {
    type: 'png',
    width: DEFAULT_WIDTH,
    height: DEFAULT_HEIGHT,
    quality: DEFAULT_QUALITY,
    timeout: DEFAULT_TIMEOUT,
    input: null,
    output: null
  };

  const parsedArgs = args.slice(2); // Remove node and script path

  for (let i = 0; i < parsedArgs.length; i++) {
    const arg = parsedArgs[i];

    switch (arg) {
      case '--help':
      case '-h':
        showHelp();
        process.exit(0);
        break;
      case '--version':
        showVersion();
        process.exit(0);
        break;
      case '-t':
      case '--type':
        i++;
        if (parsedArgs[i]) {
          const type = parsedArgs[i].toLowerCase().replace('.', '');
          if (SUPPORTED_TYPES.includes(type)) {
            options.type = type === 'jpg' ? 'jpeg' : type;
          } else {
            console.error(`Error: Unsupported format '${parsedArgs[i]}'. Supported: ${SUPPORTED_TYPES.join(', ')}`);
            process.exit(1);
          }
        }
        break;
      case '--width':
        i++;
        options.width = parseInt(parsedArgs[i], 10);
        if (isNaN(options.width) || options.width < 1) {
          console.error('Error: Width must be a positive number');
          process.exit(1);
        }
        break;
      case '--height':
        i++;
        options.height = parseInt(parsedArgs[i], 10);
        if (isNaN(options.height) || options.height < 1) {
          console.error('Error: Height must be a positive number');
          process.exit(1);
        }
        break;
      case '-q':
      case '--quality':
        i++;
        options.quality = parseFloat(parsedArgs[i]);
        if (isNaN(options.quality) || options.quality < 0 || options.quality > 100) {
          console.error('Error: Quality must be a number between 0 and 100');
          process.exit(1);
        }
        break;
      case '--timeout':
        i++;
        options.timeout = parseInt(parsedArgs[i], 10);
        if (isNaN(options.timeout) || options.timeout < 0) {
          console.error('Error: Timeout must be a positive number (milliseconds)');
          process.exit(1);
        }
        break;
      default:
        if (!arg.startsWith('-')) {
          if (!options.input) {
            options.input = arg;
          } else if (!options.output) {
            options.output = arg;
          }
        }
        break;
    }
  }

  return options;
}

/**
 * Wrap HTML content with resolution styles
 * Ensures the content fills the entire viewport
 */
function wrapHtml(html, width, height) {
  // Remove any existing viewport/style tags from the original HTML
  // and replace mindmap sizing to use percentages
  let processedHtml = html
    // Remove viewport meta that might conflict
    .replace(/<meta[^>]*viewport[^>]*>/gi, '')
    // Replace mindmap 100vw/100vh with 100% to fill container
    .replace(/#mindmap\s*\{[^}]*width:\s*[^;]*vw[^}]*\}/gi, '#mindmap { width: 100%; height: 100%; }')
    .replace(/#mindmap\s*\{[^}]*height:\s*[^;]*vh[^}]*\}/gi, '#mindmap { width: 100%; height: 100%; }');

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=${width}, height=${height}">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      width: ${width}px;
      height: ${height}px;
      overflow: hidden;
      background-color: white;
    }
    #mindmap {
      width: 100%;
      height: 100%;
      display: block;
    }
  </style>
</head>
<body>
${processedHtml}
</body>
</html>`;
}

/**
 * Main conversion function
 */
async function convert(options) {
  // Validate input file
  if (!options.input) {
    console.error('Error: Input HTML file is required');
    console.log('Run with --help for usage information');
    process.exit(1);
  }

  // Check if input file exists
  if (!fs.existsSync(options.input)) {
    console.error(`Error: Input file '${options.input}' does not exist`);
    process.exit(1);
  }

  // Read input HTML
  let htmlContent = fs.readFileSync(options.input, 'utf-8');

  // Generate output filename if not provided
  if (!options.output) {
    const inputBasename = path.basename(options.input, path.extname(options.input));
    options.output = path.join(path.dirname(options.input), `${inputBasename}.${options.type}`);
  }

  // Ensure output has correct extension
  const outputExt = path.extname(options.output).toLowerCase().replace('.', '');
  if (!SUPPORTED_TYPES.includes(outputExt)) {
    options.output = options.output.replace(/\.[^/.]+$/, '') + `.${options.type}`;
  }

  // Wrap HTML with resolution styles
  htmlContent = wrapHtml(htmlContent, options.width, options.height);

  console.log(`Converting HTML to ${options.type.toUpperCase()}...`);
  console.log(`  Input:  ${options.input}`);
  console.log(`  Output: ${options.output}`);
  console.log(`  Resolution: ${options.width}x${options.height}`);
  if (options.type === 'jpeg') {
    console.log(`  Quality: ${options.quality}`);
  }
  console.log(`  Timeout: ${options.timeout}ms`);

  try {
    const imageBuffer = await nodeHtmlToImage({
      output: options.output,
      html: htmlContent,
      type: options.type,
      quality: options.quality,
      timeout: options.timeout,
      viewport: {
        width: options.width,
        height: options.height
      },
      puppeteerArgs: {
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      }
    });

    console.log(`\nImage created successfully: ${options.output}`);

    // Also return buffer for programmatic use
    return imageBuffer;
  } catch (error) {
    console.error('Error during conversion:', error.message);
    process.exit(1);
  }
}

// Main execution
const options = parseArgs(process.argv);
await convert(options);
