#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Optimized recategorization of articles based on exact tag matching."""

import os
import re


def parse_tags(tags_line):
    """Parse tags from a Tags: line and return a list of cleaned tags."""
    if not tags_line or not tags_line.startswith("Tags:"):
        return []

    # Extract the tags part after "Tags:"
    tags_part = tags_line.split(":", 1)[1].strip()
    if not tags_part:
        return []

    # Split by comma and clean each tag
    tags = [tag.strip() for tag in tags_part.split(",") if tag.strip()]
    return tags


def get_category_from_tags(tags):
    """
    Determine category based on exact tag matches (case-insensitive).

    Args:
        tags: List of tag strings

    Returns:
        Category string ("tech", "music", or None)
    """
    if not tags:
        return None

    # Convert all tags to lowercase for case-insensitive comparison
    tags_lower = [tag.lower() for tag in tags]

    # Check for exact matches (case-insensitive)
    has_tech_tag = "tech" in tags_lower
    has_classical_music_tag = "classical music" in tags_lower

    # Handle cases with both tags - prioritize tech as it's more specific
    if has_tech_tag and has_classical_music_tag:
        # Both tags present - use tech as priority
        return "tech"
    elif has_tech_tag:
        return "tech"
    elif has_classical_music_tag:
        return "music"
    else:
        return None


def find_metadata_insert_position(lines):
    """Find the best position to insert Category metadata."""
    # Look for Slug line first
    for i, line in enumerate(lines):
        if line.startswith("Slug:"):
            return i + 1

    # If no Slug, look for Date line
    for i, line in enumerate(lines):
        if line.startswith("Date:"):
            return i + 1

    # If neither found, insert after Title
    for i, line in enumerate(lines):
        if line.startswith("Title:"):
            return i + 1

    # Fallback: insert at beginning
    return 0


def update_article_category(file_path):
    """
    Update article category based on tags.

    Returns:
        Tuple (title, new_category) if updated, None if no change needed
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # Find existing metadata
    tags_line = None
    category_line_idx = None
    title_line = None

    for i, line in enumerate(lines):
        if line.startswith("Tags:"):
            tags_line = line
        elif line.startswith("Category:"):
            category_line_idx = i
        elif line.startswith("Title:"):
            title_line = line

    if not tags_line:
        return None

    # Parse tags and determine category
    tags = parse_tags(tags_line)
    new_category = get_category_from_tags(tags)

    if not new_category:
        return None

    # Get current category if it exists
    current_category = None
    if category_line_idx is not None:
        current_category_line = lines[category_line_idx]
        if current_category_line.startswith("Category:"):
            current_category = current_category_line.split(":", 1)[1].strip()

    # Only update if category changed or doesn't exist
    if current_category == new_category:
        return None

    # Create new category line
    category_str = f"Category: {new_category}"

    if category_line_idx is not None:
        # Replace existing category line
        lines[category_line_idx] = category_str
    else:
        # Insert new category line
        insert_pos = find_metadata_insert_position(lines)
        lines.insert(insert_pos, category_str)

    # Write back the updated content
    new_content = "\n".join(lines)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    # Extract title for reporting
    title = "Unknown"
    if title_line:
        title_match = re.match(r"Title:\s*(.*)", title_line)
        if title_match:
            title = title_match.group(1).strip()

    return (title, new_category)


def main():
    """Process all markdown articles in the content directory."""
    content_dir = "content"

    tech_count = 0
    music_count = 0
    processed_files = []

    # Get all markdown files
    markdown_files = []
    for filename in os.listdir(content_dir):
        if filename.endswith(".markdown") or filename.endswith(".md"):
            markdown_files.append(filename)

    # Process files
    for filename in sorted(markdown_files):
        file_path = os.path.join(content_dir, filename)
        try:
            result = update_article_category(file_path)
            if result:
                title, category = result
                processed_files.append((filename, title, category))
                if category == "tech":
                    tech_count += 1
                elif category == "music":
                    music_count += 1
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # Report results
    print("Optimized recategorization complete:")
    print(f"  Tech articles: {tech_count}")
    print(f"  Music articles: {music_count}")
    print(f"  Total processed: {len(processed_files)}")

    # Optional: Show detailed results
    if processed_files:
        print("\nProcessed files:")
        for filename, title, category in processed_files[:10]:  # Show first 10
            print(f"  {filename} -> {category}")
        if len(processed_files) > 10:
            print(f"  ... and {len(processed_files) - 10} more")


if __name__ == "__main__":
    main()
