# Theme System Documentation

## Overview

The City Map Poster Generator uses a JSON-based theme system that provides complete control over the visual appearance of generated map posters. Each theme defines colors for all map elements including roads, water bodies, parks, background, and typography.

## Theme Architecture

### File Structure

Themes are stored as JSON files in the [`themes/`](../themes/) directory:

```
themes/
├── feature_based.json   (default theme)
├── noir.json
├── blueprint.json
├── warm_beige.json
└── ... (17 total themes)
```

### Loading Mechanism

Themes are loaded via the [`load_theme()`](../create_map_poster.py:66) function:

```python
THEME = load_theme("noir")  # Loads themes/noir.json
```

## JSON Schema

### Required Properties

Every theme JSON file must include the following properties:

```json
{
  "name": "Display Name",
  "description": "Theme description (optional)",
  "bg": "#FFFFFF",
  "text": "#000000",
  "gradient_color": "#FFFFFF",
  "water": "#C0C0C0",
  "parks": "#F0F0F0",
  "road_motorway": "#0A0A0A",
  "road_primary": "#1A1A1A",
  "road_secondary": "#2A2A2A",
  "road_tertiary": "#3A3A3A",
  "road_residential": "#4A4A4A",
  "road_default": "#3A3A3A"
}
```

### Property Reference

| Property | Type | Required | Purpose | Rendering Layer |
|----------|------|----------|---------|-----------------|
| `name` | string | Yes | Display name shown in CLI | N/A |
| `description` | string | No | Human-readable description | N/A |
| `bg` | hex color | Yes | Canvas background color | Z=0 (base) |
| `text` | hex color | Yes | Typography and labels | Z=11 (top) |
| `gradient_color` | hex color | Yes | Fade overlay color (usually matches `bg`) | Z=10 |
| `water` | hex color | Yes | Rivers, lakes, oceans | Z=1 |
| `parks` | hex color | Yes | Parks, green spaces, grass | Z=2 |
| `road_motorway` | hex color | Yes | Motorways, freeways, interstates | Z=3 |
| `road_primary` | hex color | Yes | Primary roads, major arterials | Z=3 |
| `road_secondary` | hex color | Yes | Secondary roads | Z=3 |
| `road_tertiary` | hex color | Yes | Tertiary/collector roads | Z=3 |
| `road_residential` | hex color | Yes | Residential streets, local roads | Z=3 |
| `road_default` | hex color | Yes | Fallback for unclassified roads | Z=3 |

### Color Format

**All colors must be 6-digit hexadecimal** format with `#` prefix:

```json
✅ Valid:   "#FFFFFF", "#000000", "#1A3A5C"
❌ Invalid: "FFFFFF", "#FFF", "rgb(255,255,255)"
```

## Road Hierarchy Mapping

### OSM Highway Types

The theme system maps OpenStreetMap highway classifications to theme colors:

| Theme Property | OSM Highway Types | Typical Usage | Line Width |
|----------------|-------------------|---------------|------------|
| `road_motorway` | `motorway`, `motorway_link` | Interstates, freeways, expressways | 1.2 pts |
| `road_primary` | `trunk`, `trunk_link`, `primary`, `primary_link` | Major arterial roads, state highways | 1.0 pts |
| `road_secondary` | `secondary`, `secondary_link` | Secondary arterials, county roads | 0.8 pts |
| `road_tertiary` | `tertiary`, `tertiary_link` | Collector roads, minor arterials | 0.6 pts |
| `road_residential` | `residential`, `living_street`, `unclassified` | Local streets, residential areas | 0.4 pts |
| `road_default` | All other types | Catch-all for unusual classifications | 0.6 pts |

### Visual Hierarchy

**Design Principle**: Road colors should create visual hierarchy that guides the eye from major roads (prominent) to minor streets (subtle).

**Common Strategies**:

1. **Contrast-based**: Darker colors for major roads, lighter for minor
2. **Saturation-based**: High saturation for major roads, low for minor
3. **Hue-based**: Different colors for different road types

## Creating Custom Themes

### Step-by-Step Guide

#### 1. Choose a Color Palette

Start with a cohesive color palette (3-5 base colors):

```
Example: Ocean Theme
- Base: Light blue-gray (#F0F8FA)
- Accent: Deep teal (#1A5F7A)
- Gradient: Blues from dark to light
```

#### 2. Create Theme File

Create a new JSON file in the `themes/` directory:

```bash
themes/my_custom_theme.json
```

#### 3. Define Base Colors

Start with background and text (highest contrast):

```json
{
  "name": "My Custom Theme",
  "description": "Description of the aesthetic",
  "bg": "#F0F8FA",
  "text": "#1A5F7A",
  "gradient_color": "#F0F8FA"
}
```

**Tip**: `gradient_color` should typically match `bg` for seamless fade.

#### 4. Add Feature Colors

Define water and parks (should contrast with background but remain subtle):

```json
{
  "water": "#B8D8E8",
  "parks": "#D8EAE8"
}
```

**Guidelines**:
- Water: Often blue/gray tones, slightly darker than parks
- Parks: Green/beige tones, lighter and less prominent

#### 5. Create Road Color Gradient

Define 5 road colors forming a gradient from prominent to subtle:

```json
{
  "road_motorway": "#1A5F7A",    // Darkest/most saturated
  "road_primary": "#2A7A9A",     // 
  "road_secondary": "#4A9AB8",   // Middle tone
  "road_tertiary": "#70B8D0",    //
  "road_residential": "#A0D0E0", // Lightest/least saturated
  "road_default": "#4A9AB8"      // Usually matches secondary
}
```

#### 6. Test Your Theme

```bash
python create_map_poster.py -c "New York" -C "USA" -t my_custom_theme -d 12000
```

### Complete Example

[`themes/ocean.json`](../themes/ocean.json):

```json
{
  "name": "Ocean",
  "description": "Various blues and teals - perfect for coastal cities",
  "bg": "#F0F8FA",
  "text": "#1A5F7A",
  "gradient_color": "#F0F8FA",
  "water": "#B8D8E8",
  "parks": "#D8EAE8",
  "road_motorway": "#1A5F7A",
  "road_primary": "#2A7A9A",
  "road_secondary": "#4A9AB8",
  "road_tertiary": "#70B8D0",
  "road_residential": "#A0D0E0",
  "road_default": "#4A9AB8"
}
```

## Color Theory Considerations

### Contrast Ratios

Ensure sufficient contrast between elements for visual clarity:

**Recommended Minimum Contrasts**:
- Background ↔ Text: 7:1 (WCAG AAA)
- Background ↔ Major roads: 4.5:1 (WCAG AA)
- Background ↔ Minor roads: 3:1 (minimum)

**Tools**:
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Coolors Contrast Checker](https://coolors.co/contrast-checker)

### Color Harmony

**Recommended Approaches**:

1. **Monochromatic**: Single hue with varying saturation/lightness
   - Example: [`monochrome_blue.json`](../themes/monochrome_blue.json)
   - Pros: Cohesive, professional
   - Cons: Can lack visual interest

2. **Analogous**: Colors adjacent on color wheel
   - Example: [`sunset.json`](../themes/sunset.json) (orange-pink-peach)
   - Pros: Harmonious, natural gradients
   - Cons: Low contrast if not careful

3. **Complementary**: Opposite colors on wheel
   - Example: [`neon_cyberpunk.json`](../themes/neon_cyberpunk.json) (cyan-magenta)
   - Pros: High visual impact
   - Cons: Can be overwhelming

4. **Neutral with Accent**: Grayscale base with single accent color
   - Example: [`japanese_ink.json`](../themes/japanese_ink.json)
   - Pros: Sophisticated, focused
   - Cons: Requires careful accent placement

### Saturation Balance

**General Guidelines**:
- **High saturation**: Use sparingly for accents (motorways, text)
- **Medium saturation**: Road hierarchy middle tones
- **Low saturation**: Background, minor roads, features

**Example Saturation Gradient** (HSL format):
```
road_motorway:    hsl(200, 75%, 30%)  // High saturation
road_primary:     hsl(200, 60%, 40%)
road_secondary:   hsl(200, 45%, 50%)  // Medium
road_tertiary:    hsl(200, 30%, 60%)
road_residential: hsl(200, 20%, 70%)  // Low saturation
```

### Accessibility

**Considerations**:
- **Color blindness**: Test with simulators (protanopia, deuteranopia, tritanopia)
- **Print vs. screen**: Colors appear different in print (test CMYK conversion)
- **Lighting**: Designs should work in bright and dim viewing conditions

**Tools**:
- [Coblis Color Blindness Simulator](https://www.color-blindness.com/coblis-color-blindness-simulator/)
- [Adobe Color Accessibility Tools](https://color.adobe.com/create/color-accessibility)

## Theme Gallery

Complete reference of all 17 built-in themes with visual descriptions and use cases.

---

### 1. feature_based

**File**: [`themes/feature_based.json`](../themes/feature_based.json)

**Description**: Different shades for different road types and features with clear hierarchy

**Color Palette**:
- Background: `#FFFFFF` (Pure white)
- Text: `#000000` (Black)
- Water: `#C0C0C0` (Silver)
- Parks: `#F0F0F0` (Light gray)
- Roads: Black gradient (#0A0A0A → #4A4A4A)

**Aesthetic**: Classic, high-contrast, print-ready

**Best For**: 
- Technical documentation
- First-time users (default theme)
- Cities with strong grid patterns

---

### 2. noir

**File**: [`themes/noir.json`](../themes/noir.json)

**Description**: Pure black background with white/gray roads - modern gallery aesthetic

**Color Palette**:
- Background: `#000000` (Pure black)
- Text: `#FFFFFF` (White)
- Water: `#0A0A0A` (Near black)
- Parks: `#111111` (Very dark gray)
- Roads: White to gray gradient (#FFFFFF → #505050)

**Aesthetic**: Dramatic, high-contrast, modern art

**Best For**:
- Gallery displays
- Grid cities (NYC, Chicago)
- Modern/minimalist design

---

### 3. blueprint

**File**: [`themes/blueprint.json`](../themes/blueprint.json)

**Description**: Classic architectural blueprint - technical drawing aesthetic

**Color Palette**:
- Background: `#1A3A5C` (Deep navy blue)
- Text: `#E8F4FF` (Light cyan-white)
- Water: `#0F2840` (Darker navy)
- Parks: `#1E4570` (Medium navy)
- Roads: Cyan gradient (#E8F4FF → #5A96C0)

**Aesthetic**: Technical, architectural, vintage

**Best For**:
- Architectural presentations
- Historical cities
- Professional/technical contexts

---

### 4. warm_beige

**File**: [`themes/warm_beige.json`](../themes/warm_beige.json)

**Description**: Earthy warm neutrals with sepia tones - vintage map aesthetic

**Color Palette**:
- Background: `#F5F0E8` (Warm beige)
- Text: `#6B5B4F` (Brown)
- Water: `#DDD5C8` (Sand)
- Parks: `#E8E4D8` (Light beige)
- Roads: Brown gradient (#8B7355 → #D9CFC2)

**Aesthetic**: Vintage, warm, nostalgic

**Best For**:
- European cities
- Vintage/retro design
- Warm, inviting presentations

---

### 5. terracotta

**File**: [`themes/terracotta.json`](../themes/terracotta.json)

**Description**: Mediterranean warmth - burnt orange and clay tones on cream

**Color Palette**:
- Background: `#F5EDE4` (Cream)
- Text: `#8B4513` (Saddle brown)
- Water: `#A8C4C4` (Muted teal)
- Parks: `#E8E0D0` (Light tan)
- Roads: Terracotta gradient (#A0522D → #E5C4B0)

**Aesthetic**: Mediterranean, earthy, warm

**Best For**:
- Mediterranean cities (Marrakech, Barcelona)
- Desert/arid locations
- Warm color schemes

---

### 6. forest

**File**: [`themes/forest.json`](../themes/forest.json)

**Description**: Deep greens and sage tones - organic botanical aesthetic

**Color Palette**:
- Background: `#F0F4F0` (Pale mint)
- Text: `#2D4A3E` (Dark green)
- Water: `#B8D4D4` (Muted teal)
- Parks: `#D4E8D4` (Light sage)
- Roads: Green gradient (#2D4A3E → #A0C8B0)

**Aesthetic**: Natural, organic, botanical

**Best For**:
- Cities with extensive parks
- Environmental/sustainability themes
- Nature-focused presentations

---

### 7. sunset

**File**: [`themes/sunset.json`](../themes/sunset.json)

**Description**: Warm oranges and pinks on soft peach - dreamy golden hour aesthetic

**Color Palette**:
- Background: `#FDF5F0` (Soft peach)
- Text: `#C45C3E` (Burnt sienna)
- Water: `#F0D8D0` (Pale pink)
- Parks: `#F8E8E0` (Light peach)
- Roads: Warm gradient (#C45C3E → #F5D0C8)

**Aesthetic**: Dreamy, romantic, warm

**Best For**:
- Coastal cities at golden hour
- Romantic/artistic presentations
- Wedding/event decor

---

### 8. midnight_blue

**File**: [`themes/midnight_blue.json`](../themes/midnight_blue.json)

**Description**: Deep navy background with gold/copper roads - luxury atlas aesthetic

**Color Palette**:
- Background: `#0A1628` (Midnight navy)
- Text: `#D4AF37` (Gold)
- Water: `#061020` (Darker navy)
- Parks: `#0F2235` (Deep blue)
- Roads: Gold to brown gradient (#D4AF37 → #6B5B4F)

**Aesthetic**: Luxurious, elegant, high-end

**Best For**:
- Luxury presentations
- Night city views
- Premium/upscale contexts

---

### 9. neon_cyberpunk

**File**: [`themes/neon_cyberpunk.json`](../themes/neon_cyberpunk.json)

**Description**: Dark background with electric pink/cyan - bold night city vibes

**Color Palette**:
- Background: `#0D0D1A` (Deep purple-black)
- Text: `#00FFFF` (Cyan)
- Water: `#0A0A15` (Dark purple)
- Parks: `#151525` (Dark purple-gray)
- Roads: Magenta-cyan gradient (#FF00FF → #006870)

**Aesthetic**: Futuristic, bold, high-energy

**Best For**:
- Tech cities (Tokyo, Singapore, Seoul)
- Futuristic/sci-fi themes
- Modern digital presentations

---

### 10. gradient_roads

**File**: [`themes/gradient_roads.json`](../themes/gradient_roads.json)

**Description**: Smooth gradient from dark center to light edges with subtle features

**Color Palette**:
- Background: `#FFFFFF` (White)
- Text: `#000000` (Black)
- Water: `#D5D5D5` (Light gray)
- Parks: `#EFEFEF` (Very light gray)
- Roads: Black gradient (#050505 → #555555)

**Aesthetic**: Subtle, refined, gradient-focused

**Best For**:
- Highlighting urban density
- Artistic/abstract presentations
- Dense city centers

---

### 11. contrast_zones

**File**: [`themes/contrast_zones.json`](../themes/contrast_zones.json)

**Description**: Strong contrast showing urban density - darker in center, lighter at edges

**Color Palette**:
- Background: `#FFFFFF` (White)
- Text: `#000000` (Black)
- Water: `#B0B0B0` (Medium gray)
- Parks: `#ECECEC` (Very light gray)
- Roads: Black gradient (#000000 → #5A5A5A)

**Aesthetic**: High-contrast, analytical

**Best For**:
- Urban density analysis
- Strong visual impact
- Cities with clear center/periphery

---

### 12. autumn

**File**: [`themes/autumn.json`](../themes/autumn.json)

**Description**: Burnt oranges, deep reds, golden yellows - seasonal warmth

**Color Palette**:
- Background: `#FBF7F0` (Cream)
- Text: `#8B4513` (Saddle brown)
- Water: `#D8CFC0` (Tan)
- Parks: `#E8E0D0` (Light tan)
- Roads: Autumn gradient (#8B2500 → #E8C888)

**Aesthetic**: Seasonal, warm, cozy

**Best For**:
- Fall/autumn themes
- Warm color preferences
- Cities with autumn foliage

---

### 13. copper_patina

**File**: [`themes/copper_patina.json`](../themes/copper_patina.json)

**Description**: Oxidized copper aesthetic - teal-green patina with copper accents

**Color Palette**:
- Background: `#E8F0F0` (Pale cyan)
- Text: `#2A5A5A` (Dark teal)
- Water: `#C0D8D8` (Light teal)
- Parks: `#D8E8E0` (Pale mint)
- Roads: Copper-teal gradient (#B87333 → #A8CCCC)

**Aesthetic**: Industrial, aged, unique

**Best For**:
- Industrial cities
- Unique color palette
- Historical/aged aesthetic

---

### 14. japanese_ink

**File**: [`themes/japanese_ink.json`](../themes/japanese_ink.json)

**Description**: Traditional ink wash inspired - minimalist with subtle red accent

**Color Palette**:
- Background: `#FAF8F5` (Off-white)
- Text: `#2C2C2C` (Charcoal)
- Water: `#E8E4E0` (Light gray)
- Parks: `#F0EDE8` (Very light gray)
- Roads: Gray gradient with red accent (#8B2500 motorway, #4A4A4A → #B8B8B8)

**Aesthetic**: Minimalist, artistic, Japanese-inspired

**Best For**:
- Japanese cities (Tokyo, Kyoto)
- Minimalist design
- Artistic presentations

---

### 15. ocean

**File**: [`themes/ocean.json`](../themes/ocean.json)

**Description**: Various blues and teals - perfect for coastal cities

**Color Palette**:
- Background: `#F0F8FA` (Light cyan)
- Text: `#1A5F7A` (Deep teal)
- Water: `#B8D8E8` (Light blue)
- Parks: `#D8EAE8` (Pale mint)
- Roads: Blue gradient (#1A5F7A → #A0D0E0)

**Aesthetic**: Coastal, fresh, aquatic

**Best For**:
- Coastal/waterfront cities
- Ocean themes
- Beach/vacation contexts

---

### 16. pastel_dream

**File**: [`themes/pastel_dream.json`](../themes/pastel_dream.json)

**Description**: Soft muted pastels with dusty blues and mauves - dreamy artistic aesthetic

**Color Palette**:
- Background: `#FAF7F2` (Warm off-white)
- Text: `#5D5A6D` (Dusty purple)
- Water: `#D4E4ED` (Pale blue)
- Parks: `#E8EDE4` (Pale mint)
- Roads: Pastel gradient (#7B8794 → #D8D2D8)

**Aesthetic**: Dreamy, soft, artistic

**Best For**:
- Artistic presentations
- Soft/gentle aesthetics
- Radial pattern cities (Paris)

---

### 17. monochrome_blue

**File**: [`themes/monochrome_blue.json`](../themes/monochrome_blue.json)

**Description**: Single blue color family with varying saturation - clean and cohesive

**Color Palette**:
- Background: `#F5F8FA` (Very light blue)
- Text: `#1A3A5C` (Dark blue)
- Water: `#D0E0F0` (Light blue)
- Parks: `#E0EAF2` (Very light blue)
- Roads: Blue gradient (#1A3A5C → #A8C4E0)

**Aesthetic**: Cohesive, professional, monochromatic

**Best For**:
- Professional presentations
- Clean design
- Cohesive color schemes

---

## Best Practices

### Theme Design Guidelines

1. **Start with purpose**: Define the mood/aesthetic before choosing colors
2. **Test contrast**: Ensure readability at various sizes/distances
3. **Consider context**: Where will the poster be displayed? (screen/print/gallery)
4. **Iterate**: Generate test posters with different cities to verify versatility
5. **Document**: Include clear `name` and `description` fields

### Common Pitfalls

❌ **Too little contrast**: Roads blend into background
```json
// BAD: Roads barely visible
"bg": "#F0F0F0",
"road_residential": "#E8E8E8"  // Only 8% difference
```

✅ **Good contrast**: Clear visual hierarchy
```json
// GOOD: Clear distinction
"bg": "#F0F0F0",
"road_residential": "#A0A0A0"  // 37% difference
```

---

❌ **Inconsistent saturation**: Jarring color transitions
```json
// BAD: Mismatched saturation levels
"road_motorway": "#FF0000",    // 100% saturation
"road_primary": "#808080"      // 0% saturation
```

✅ **Consistent saturation**: Smooth gradient
```json
// GOOD: Gradual saturation change
"road_motorway": "#CC3333",    // 60% saturation
"road_primary": "#AA5555"      // 40% saturation
```

---

❌ **Water/parks too prominent**: Compete with roads
```json
// BAD: Features overpower street network
"bg": "#FFFFFF",
"water": "#0000FF",    // Pure blue - too strong
"parks": "#00FF00"     // Pure green - too strong
```

✅ **Subtle features**: Support without dominating
```json
// GOOD: Subtle supporting elements
"bg": "#FFFFFF",
"water": "#C0D8E8",    // Muted blue
"parks": "#D8E8D0"     // Muted green
```

### Testing Checklist

Before finalizing a theme, test with:

- [ ] **Grid city** (New York, Chicago): Tests line clarity
- [ ] **Organic city** (Tokyo, London): Tests density handling  
- [ ] **Coastal city** (San Francisco, Sydney): Tests water rendering
- [ ] **Small city** (Venice, Bruges): Tests feature visibility
- [ ] **Large metro** (Mumbai, São Paulo): Tests scale/performance

## Advanced Techniques

### Dynamic Color Generation

For programmatic theme creation:

```python
def generate_gradient_theme(base_color, bg_color="#FFFFFF"):
    """Generate theme with gradient from base_color to white"""
    import colorsys
    
    # Parse base color
    r, g, b = int(base_color[1:3], 16), int(base_color[3:5], 16), int(base_color[5:7], 16)
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    
    # Generate gradient
    theme = {
        "bg": bg_color,
        "text": base_color,
        "gradient_color": bg_color,
        "water": hsv_to_hex(h, s*0.3, v*0.9),
        "parks": hsv_to_hex(h, s*0.2, v*0.95)
    }
    
    # Road gradient
    for i, road_type in enumerate(["motorway", "primary", "secondary", "tertiary", "residential"]):
        factor = 1 - (i * 0.2)  # 1.0, 0.8, 0.6, 0.4, 0.2
        theme[f"road_{road_type}"] = hsv_to_hex(h, s*factor, v)
    
    theme["road_default"] = theme["road_secondary"]
    return theme
```

### Seasonal Variations

Create theme sets for different seasons:

```
themes/
├── spring_green.json
├── summer_bright.json
├── autumn.json         (already exists)
└── winter_blue.json
```

### City-Specific Themes

Design themes optimized for specific cities:

```
themes/
├── tokyo_neon.json        # High-density, futuristic
├── venice_aqua.json       # Water-focused
├── paris_haussman.json    # Radial elegance
└── nyc_grid.json          # Strong geometric
```

## Troubleshooting

### Common Issues

**Issue**: Theme not appearing in `--list-themes`
- **Cause**: File not in `themes/` directory or wrong extension
- **Solution**: Ensure file is `themes/my_theme.json` (not `.txt` or other)

**Issue**: Error: "Theme file not found"
- **Cause**: Typo in theme name
- **Solution**: Use `--list-themes` to see exact names

**Issue**: Colors look different in output
- **Cause**: Color space conversion (RGB vs CMYK)
- **Solution**: Test print output, adjust colors if needed

**Issue**: Roads invisible on background
- **Cause**: Insufficient contrast
- **Solution**: Increase contrast ratio between background and roads

## See Also

- [Technical Overview](TECHNICAL_OVERVIEW.md) - System architecture
- [API Reference](API_REFERENCE.md) - Function documentation
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Installation instructions