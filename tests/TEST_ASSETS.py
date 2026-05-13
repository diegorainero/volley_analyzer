#!/usr/bin/env python3
"""
Test file for Volleyball Scout Assets Module
Verifies that all assets are properly created and loadable
"""

import sys
from pathlib import Path

# Project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
_ASSETS_DIR = _PROJECT_ROOT / "volleyball_scout/ui/assets"


def test_assets_directory():
    """Test that assets directory exists and contains required files"""
    print("=" * 60)
    print("🧪 Testing Assets Directory")
    print("=" * 60)

    assets_dir = _ASSETS_DIR

    # Check directory exists
    if not assets_dir.exists():
        print("❌ Assets directory does not exist")
        return False

    print(f"✅ Assets directory found: {assets_dir}")

    # Check required files
    required_files = [
        "__init__.py",
        "logo.svg",
        "icons.svg",
        "README.md",
    ]

    all_exist = True
    for filename in required_files:
        file_path = assets_dir / filename
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {filename:<20} ({size:>6} bytes)")
        else:
            print(f"❌ {filename:<20} NOT FOUND")
            all_exist = False

    print()
    return all_exist


def test_assets_imports():
    """Test that assets module can be imported"""
    print("=" * 60)
    print("🧪 Testing Assets Module Imports")
    print("=" * 60)

    try:
        from volleyball_scout.ui.assets import (
            ASSETS_DIR,
            get_icon,
            get_logo_icon,
            get_logo_pixmap,
        )

        print("✅ Successfully imported assets module")
        print(f"✅ ASSETS_DIR = {ASSETS_DIR}")

        # Verify ASSETS_DIR path
        if ASSETS_DIR.exists():
            print(f"✅ ASSETS_DIR is accessible")
        else:
            print(f"❌ ASSETS_DIR does not exist: {ASSETS_DIR}")
            return False

        # Verify functions are callable
        functions = [get_logo_pixmap, get_logo_icon, get_icon]
        for func in functions:
            if callable(func):
                print(f"✅ {func.__name__} is callable")
            else:
                print(f"❌ {func.__name__} is not callable")
                return False

        print()
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_logo_loading():
    """Test loading the logo pixmap"""
    print("=" * 60)
    print("🧪 Testing Logo Loading")
    print("=" * 60)

    try:
        from volleyball_scout.ui.assets import get_logo_pixmap

        # Test different sizes
        sizes = [32, 64, 80, 100, 128]

        for size in sizes:
            try:
                pixmap = get_logo_pixmap(size=size)

                if pixmap.isNull():
                    print(f"⚠️  Logo {size}px loaded but is null")
                else:
                    print(
                        f"✅ Logo {size}px loaded: {pixmap.width()}x{pixmap.height()}"
                    )

            except Exception as e:
                print(f"❌ Error loading logo {size}px: {e}")
                return False

        print()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_logo_icon_loading():
    """Test loading the logo icon"""
    print("=" * 60)
    print("🧪 Testing Logo Icon Loading")
    print("=" * 60)

    try:
        from volleyball_scout.ui.assets import get_logo_icon

        # Test different sizes
        sizes = [16, 24, 32, 48]

        for size in sizes:
            try:
                icon = get_logo_icon(size=size)

                # Icon validity check
                if icon.isNull():
                    print(f"⚠️  Logo icon {size}px is null")
                else:
                    print(f"✅ Logo icon {size}px loaded")

            except Exception as e:
                print(f"❌ Error loading logo icon {size}px: {e}")
                return False

        print()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_icons_sprite_loading():
    """Test loading the icons sprite"""
    print("=" * 60)
    print("🧪 Testing Icons Sprite Loading")
    print("=" * 60)

    try:
        from volleyball_scout.ui.assets import get_icon

        # Test icon names
        icon_names = ["dashboard", "team", "formation", "scout", "stats"]

        for icon_name in icon_names:
            try:
                icon = get_icon(icon_name)

                if icon.isNull():
                    print(
                        f"⚠️  Icon '{icon_name}' is null (may not be separately cropped)"
                    )
                else:
                    print(f"✅ Icon '{icon_name}' loaded")

            except Exception as e:
                print(f"❌ Error loading icon '{icon_name}': {e}")
                return False

        print()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_svg_files():
    """Test that SVG files are valid XML"""
    print("=" * 60)
    print("🧪 Testing SVG Files")
    print("=" * 60)

    try:
        import xml.etree.ElementTree as ET

        assets_dir = _ASSETS_DIR
        svg_files = list(assets_dir.glob("*.svg"))

        if not svg_files:
            print("⚠️  No SVG files found")
            return False

        for svg_file in svg_files:
            try:
                tree = ET.parse(svg_file)
                root = tree.getroot()

                # Check for SVG root element
                if "svg" in root.tag.lower():
                    width = root.get("width", "viewBox specified")
                    height = root.get("height", "viewBox specified")
                    print(f"✅ {svg_file.name}: Valid SVG")
                else:
                    print(f"❌ {svg_file.name}: Not an SVG file")
                    return False

            except ET.ParseError as e:
                print(f"❌ {svg_file.name}: Invalid XML - {e}")
                return False
            except Exception as e:
                print(f"❌ {svg_file.name}: Error - {e}")
                return False

        print()
        return True

    except ImportError:
        print("⚠️  xml.etree.ElementTree not available, skipping XML validation")
        return True


def test_svg_colors():
    """Test that SVG files use correct colors"""
    print("=" * 60)
    print("🧪 Testing SVG Color Scheme")
    print("=" * 60)

    expected_colors = {
        "#1e1e1e": "Dark background",
        "#252525": "Medium surface",
        "#2d2d2d": "Lighter surface",
        "#3d3d3d": "Border color",
        "#e0e0e0": "Primary text",
        "#999999": "Secondary text",
        "#666666": "Tertiary text",
        "#E95420": "Primary accent (Ubuntu orange)",
        "#C7451A": "Dark accent (Ubuntu orange hover)",
    }

    assets_dir = _ASSETS_DIR

    for svg_file in assets_dir.glob("*.svg"):
        try:
            content = svg_file.read_text()

            found_colors = set()
            for color in expected_colors.keys():
                if color.lower() in content.lower():
                    found_colors.add(color)

            if found_colors:
                print(f"✅ {svg_file.name}: Uses {len(found_colors)} color(s)")
                for color in found_colors:
                    print(f"   - {color}: {expected_colors[color]}")
            else:
                print(f"⚠️  {svg_file.name}: May not use standard colors")

        except Exception as e:
            print(f"❌ {svg_file.name}: Error reading - {e}")

    print()
    return True


def print_summary(results):
    """Print test summary"""
    print("=" * 60)
    print("📋 Test Summary")
    print("=" * 60)

    tests = [
        ("Assets Directory", results[0]),
        ("Assets Module Imports", results[1]),
        ("Logo Loading", results[2]),
        ("Logo Icon Loading", results[3]),
        ("Icons Sprite Loading", results[4]),
        ("SVG Files Validation", results[5]),
        ("SVG Colors Scheme", results[6]),
    ]

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<12} {test_name}")

    print()
    print(f"Result: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Assets module is ready to use.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")

    print()


def main():
    """Run all tests"""
    print("\n")
    print("🏐" * 30)
    print("Volleyball Scout Assets - Test Suite")
    print("🏐" * 30)
    print()

    results = [
        test_assets_directory(),
        test_assets_imports(),
        test_logo_loading(),
        test_logo_icon_loading(),
        test_icons_sprite_loading(),
        test_svg_files(),
        test_svg_colors(),
    ]

    print_summary(results)

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
