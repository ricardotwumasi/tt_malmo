#!/bin/bash

echo "=================================================="
echo "  Installing Java 8 for Malmo/Minecraft"
echo "=================================================="
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Please install Homebrew first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "📦 Installing Java 8 (Temurin)..."
brew install --cask temurin@8

echo ""
echo "✅ Java 8 installed!"
echo ""
echo "To use Java 8 for Malmo, run:"
echo ""
echo "  export JAVA_HOME=\$(/usr/libexec/java_home -v 1.8)"
echo "  java -version"
echo ""
echo "Or add to your ~/.zshrc to make it permanent:"
echo ""
echo "  echo 'export JAVA_HOME=\$(/usr/libexec/java_home -v 1.8)' >> ~/.zshrc"
echo ""
echo "=================================================="
