#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convert Octopress markdown files to Pelican format.
Handles conversion of:
- YAML front matter (Pelican compatible)
- Liquid tags: img, imgcap, include_code, codeblock
- Image paths
- Slug generation from filename
"""

import os
import re
import sys
from pathlib import Path


def convert_frontmatter(lines):
    """Convert Jekyll front matter to Pelican format"""
    converted_lines = []
    categories = []
    tags = []
    date = None
    title = None
    summary = None

    for line in lines:
        if line.strip() == "---":
            continue
        elif line.startswith("layout:"):
            continue
        elif line.startswith("title:"):
            title = line.split(":", 1)[1].strip().strip("\"'")
            converted_lines.append(f"Title: {title}")
        elif line.startswith("date:"):
            date_str = line.split(":", 1)[1].strip()
            # Octopress date: 2016-06-03 11:22
            # Pelican expects: 2016-06-03 11:22:00
            if len(date_str.strip()) == 5:  # Date only: 2016-06-03
                date_str += " 00:00:00"
            elif len(date_str.strip()) == 16:  # Datetime: 2016-06-03 11:22
                date_str += ":00"
            converted_lines.append(f"Date: {date_str}")
            date = date_str
        elif line.startswith("categories:"):
            # Extract categories list [cat1, cat2, cat3]
            match = re.search(r"\[(.*?)\]", line)
            if match:
                cats = [c.strip().strip("\"'") for c in match.group(1).split(",")]
                categories.extend(cats)
        elif line.startswith("keywords:"):
            keywords = line.split(":", 1)[1].strip().strip("\"'")
            tags = [kw.strip() for kw in keywords.split(",")]
        elif line.startswith("description:"):
            summary = line.split(":", 1)[1].strip().strip("\"'")
            converted_lines.append(line)
        elif line.startswith("comments:"):
            continue
        elif line.startswith("published:"):
            continue
        else:
            converted_lines.append(line)

    # Add categories as Tags (Pelican uses Tags mainly)
    if categories:
        converted_lines.append(f"Tags: {', '.join(categories)}")

    # Add extracted keywords as additional tags
    if tags:
        if categories:
            converted_lines[-1] = f"Tags: {', '.join(categories + tags)}"
        else:
            converted_lines.append(f"Tags: {', '.join(tags)}")

    return converted_lines


def convert_liquid_tags(content):
    """Convert Octopress liquid tags to Pelican/markdown format"""

    # Convert {% img /images/path.png %} to markdown image syntax
    content = re.sub(r"{%\s*img\s+([^\s%]+)\s*(?:%})?", r"![image](\1)", content)

    # Convert {% imgcap /images/path.png 'caption' %} to markdown with caption
    content = re.sub(
        r'{%\s*imgcap\s+([^\s%]+)\s+[\'"](.*?)[\'"]\s*%}', r"![\2](\1)", content
    )

    # Convert {% include_code filename.ext %} to code block reference
    # For now, we'll leave a marker
    content = re.sub(
        r"{%\s*include_code\s+([^\s%]+)\s*(?:lang:\s*([^\s%]+))?\s*%}",
        r"[Code: \1]",
        content,
    )

    # Convert {% codeblock lang:xxx %}...{% endcodeblock %} to fenced code blocks
    content = re.sub(
        r"{%\s*codeblock\s+lang:(\w+)\s*%}(.*?){%\s*endcodeblock\s*%}",
        lambda m: f"```{m.group(1)}\n{m.group(2)}\n```",
        content,
        flags=re.DOTALL,
    )

    return content


def convert_file(input_path, output_path, input_filename):
    """Convert a single Octopress markdown file to Pelican format"""

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # Skip the first '---' and find the second '---'
    start_index = None
    end_index = None

    for i, line in enumerate(lines):
        if line.strip() == "---":
            if start_index is None:
                start_index = i
            else:
                end_index = i
                break

    if start_index is None or end_index is None:
        print(f"Warning: Could not find front matter in {input_path}")
        return

    # Convert front matter
    frontmatter_lines = lines[start_index + 1 : end_index]
    converted_frontmatter = convert_frontmatter(frontmatter_lines)

    # Generate slug from filename (not title)
    # Filename format: YYYY-MM-DD-title-slug.markdown
    base_name = input_filename.replace(".markdown", "").replace(".md", "")

    # Remove date prefix (YYYY-MM-DD-) - first 11 characters
    if len(base_name) >= 11:
        date_part = base_name[:4] + base_name[5:7] + base_name[8:10]  # YYYYMMDD
        title_slug = base_name[11:]  # Everything after YYYY-MM-DD-
        slug = f"{date_part}-{title_slug}"
    else:
        # If filename doesn't match expected format, use whole basename
        slug = base_name

    # Add slug to front matter
    converted_frontmatter.append(f"Slug: {slug}")

    # Get content after front matter
    body_lines = lines[end_index + 1 :]
    body_content = "\n".join(body_lines)

    # Convert liquid tags in body
    converted_body = convert_liquid_tags(body_content)

    # Write output
    output_content = "\n".join(converted_frontmatter) + "\n" + converted_body

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_content)

    print(f"Converted: {input_filename} -> slug: {slug}")


def main():
    """Main conversion function"""

    # Source directories
    source_posts_dir = "source/_posts"
    output_content_dir = "content"

    # Create output directory
    os.makedirs(output_content_dir, exist_ok=True)

    # Convert all markdown files
    count = 0
    for filename in os.listdir(source_posts_dir):
        if filename.endswith(".markdown") or filename.endswith(".md"):
            input_filename = filename
            input_path = os.path.join(source_posts_dir, filename)
            output_path = os.path.join(output_content_dir, filename)

            convert_file(input_path, output_path, input_filename)
            count += 1

    print(f"\nConversion complete! Converted {count} files.")
    print(f"Output directory: {output_content_dir}")


if __name__ == "__main__":
    main()
