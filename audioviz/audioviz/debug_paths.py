
import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Base dir: {base_dir}")

checks = [
    os.path.join(base_dir, "resources", "Roboto-Regular.ttf"),
    os.path.join(base_dir, "..", "resources", "Roboto-Regular.ttf"),
    os.path.join(base_dir, "..", "..", "resources", "Roboto-Regular.ttf"),
    "/mnt/c/audioviz/audioviz/audioviz/resources/Roboto-Regular.ttf"
]

print("Checking paths:")
for p in checks:
    exists = os.path.exists(p)
    print(f"  {p}: {exists}")
    if exists:
        print(f"    -> Found!")

print("\nListing parent dir:")
try:
    parent = os.path.dirname(base_dir)
    for item in os.listdir(parent):
        print(f"  {item}")
        if item == "resources":
             print("    Listing resources:")
             for r in os.listdir(os.path.join(parent, "resources")):
                 print(f"      {r}")
except Exception as e:
    print(f"Error listing: {e}")
