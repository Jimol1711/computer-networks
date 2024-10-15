# Create a file with 100 MB of Lorem Ipsum text
file_size_mb = 100
lorem_ipsum_text = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
    "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
    "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
    "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
    "culpa qui officia deserunt mollit anim id est laborum.\n\n"
)

# Calculate the size of one block of text
text_size = len(lorem_ipsum_text)

# Create the file and write Lorem Ipsum text until it reaches 100 MB
with open('lorem_ipsum.txt', 'w') as f:
    # Calculate how many times to write the Lorem Ipsum text
    repetitions = (file_size_mb * 1024 * 1024) // text_size
    for _ in range(repetitions):
        f.write(lorem_ipsum_text)