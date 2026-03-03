import sys
import time

def main():
    # ASCII Art Frames: Bearded Lady Dancing
    # Beard represented by '~' under the head 'O'
    frames = [
        [
            "   O   ",
            "  ~|~  ",
            "  /|\\ ",
            "  / \\ "
        ],
        [
            "   O   ",
            "  ~|~  ",
            "  -|-  ",
            "  / \\ "
        ]
    ]

    creek = "~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*"
    screen_width = 50
    
    try:
        for i in range(screen_width):
            for frame in frames:
                # Clear screen using ANSI escape codes
                sys.stdout.write("\033[2J\033[H")
                
                # Vertical spacing
                print("\n" * 5)
                
                # Horizontal movement
                print(" " * i, end="")
                
                # Draw Lady
                for line in frame:
                    print(" " * i + line)
                
                # Draw Creek below feet
                print(" " * (i + 2) + creek)
                
                sys.stdout.flush()
                time.sleep(0.15)
                
    except KeyboardInterrupt:
        pass
    finally:
        # Reset cursor and clear screen on exit
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
        print("Performance ended.")

if __name__ == "__main__":
    main()