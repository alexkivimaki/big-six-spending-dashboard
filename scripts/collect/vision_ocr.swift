import Foundation
import Vision
import AppKit

if CommandLine.arguments.count < 2 {
    fputs("Usage: swift vision_ocr.swift /path/to/image.png\n", stderr)
    exit(1)
}

let path = CommandLine.arguments.last!
let url = URL(fileURLWithPath: path)
guard let image = NSImage(contentsOf: url) else {
    fputs("Unable to load image: \(path)\n", stderr)
    exit(2)
}
guard let tiff = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiff),
      let cgImage = bitmap.cgImage else {
    fputs("Unable to build CGImage for: \(path)\n", stderr)
    exit(3)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.recognitionLanguages = ["en-GB", "en-US"]

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try handler.perform([request])

for observation in request.results ?? [] {
    if let candidate = observation.topCandidates(1).first {
        print(candidate.string)
    }
}
