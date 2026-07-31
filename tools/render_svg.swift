import AppKit
import Foundation

guard CommandLine.arguments.count == 4 else {
    fputs("Usage: render_svg.swift input.svg size output.png\n", stderr)
    exit(2)
}

let inputURL = URL(fileURLWithPath: CommandLine.arguments[1])
guard let size = Int(CommandLine.arguments[2]), size > 0 else {
    fputs("Size must be a positive integer.\n", stderr)
    exit(2)
}
let outputURL = URL(fileURLWithPath: CommandLine.arguments[3])

guard let image = NSImage(contentsOf: inputURL) else {
    fputs("Could not load SVG: \(inputURL.path)\n", stderr)
    exit(1)
}

guard let bitmap = NSBitmapImageRep(
    bitmapDataPlanes: nil,
    pixelsWide: size,
    pixelsHigh: size,
    bitsPerSample: 8,
    samplesPerPixel: 4,
    hasAlpha: true,
    isPlanar: false,
    colorSpaceName: .deviceRGB,
    bytesPerRow: 0,
    bitsPerPixel: 0
) else {
    fputs("Could not create bitmap.\n", stderr)
    exit(1)
}

bitmap.size = NSSize(width: size, height: size)
guard let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
    fputs("Could not create graphics context.\n", stderr)
    exit(1)
}

NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = context
context.imageInterpolation = .high
context.cgContext.clear(CGRect(x: 0, y: 0, width: size, height: size))
image.draw(
    in: NSRect(x: 0, y: 0, width: size, height: size),
    from: .zero,
    operation: .sourceOver,
    fraction: 1,
    respectFlipped: true,
    hints: [.interpolation: NSImageInterpolation.high]
)
context.flushGraphics()
NSGraphicsContext.restoreGraphicsState()

guard let data = bitmap.representation(using: .png, properties: [:]) else {
    fputs("Could not encode PNG.\n", stderr)
    exit(1)
}

do {
    try data.write(to: outputURL, options: .atomic)
} catch {
    fputs("Could not write PNG: \(error)\n", stderr)
    exit(1)
}
