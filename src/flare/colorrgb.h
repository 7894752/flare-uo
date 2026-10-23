/*
===========================================================================
flare (Call of Duty: United Offensive, 2004).

Distributed under the terms in COPYING (GPL version 3 or later,
with id Software's additional terms).

Single-precision RGB colors.
===========================================================================
*/
#ifndef FLARE_COLORRGB_H
#define FLARE_COLORRGB_H

/* ColorRGB supplies RGB storage and operations without construction.
 * Color3f adds value construction. */
struct Color3f;

struct ColorRGB
{
    float r, g, b;

    void operator+=(const ColorRGB &color)
    {
        r += color.r;
        g += color.g;
        b += color.b;
    }
    void operator*=(float scale);
    void operator/=(float scale);
    operator float *();
    void Clear();
    void Normalize();                               /* scales so the largest component is 1 */
    void FromBytes(const unsigned char *rgb);
    void ToBytes(unsigned char *rgb) const;
    float Luminance() const;
    inline Color3f operator*(const ColorRGB &color) const;
    inline Color3f operator*(float scale) const;
    inline Color3f operator/(float scale) const;
};

struct Color3f : ColorRGB
{
    Color3f() {}
    Color3f(const Color3f &color)
    {
        r = color.r;
        g = color.g;
        b = color.b;
    }
    Color3f(float red, float green, float blue)
    {
        r = red;
        g = green;
        b = blue;
    }
    Color3f(const ColorRGB &color)
    {
        r = color.r;
        g = color.g;
        b = color.b;
    }
    void operator=(const ColorRGB &color)
    {
        r = color.r;
        g = color.g;
        b = color.b;
    }
};

inline Color3f ColorRGB::operator*(const ColorRGB &color) const
{
    return Color3f(r * color.r, g * color.g, b * color.b);
}
inline Color3f ColorRGB::operator*(float scale) const
{
    return Color3f(r * scale, g * scale, b * scale);
}
inline Color3f ColorRGB::operator/(float scale) const
{
    scale = 1.0f / scale;
    return *this * scale;
}

#endif
