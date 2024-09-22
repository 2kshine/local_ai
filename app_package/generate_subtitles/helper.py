def format_time(seconds):
    """Convert time in seconds (float) to ASS time format (HH:MM:SS.CS)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    centiseconds = int((seconds % 1) * 100)  # Get the centiseconds from the decimal part
    seconds = int(seconds % 60)  # Get the whole seconds
    
    return f"{hours:01}:{minutes:02}:{seconds:02}.{centiseconds:02}"

def header_file(title, dimension):
    # ASS file header
    ass_header = f"""
    [Script Info]
    Title: {title}
    Original Script: Assistant
    ScriptType: v4.00
    Collisions: Normal
    PlayDepth: 0
    PlayResX: {dimension[0]}
    PlayResY: {dimension[1]}

    [V4+ Styles]
    Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, TertiaryColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, AlphaLevel, Encoding
    Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H000000FF,&H00000000,0,0,1,1.00,0.00,5,10,10,1344,0,1

    [Events]
    """
    return ass_header

