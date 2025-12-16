#!/bin/bash

# Switch to Java 8 for current terminal session
# Run this before launching Malmo/Minecraft

echo "=================================================="
echo "  Switching to Java 8"
echo "=================================================="
echo ""

# Check if Java 8 is installed
if ! /usr/libexec/java_home -v 1.8 &> /dev/null; then
    echo "❌ Java 8 not found!"
    echo ""
    echo "Please install Java 8 first:"
    echo "  ./install_java8.sh"
    exit 1
fi

# Set JAVA_HOME to Java 8
export JAVA_HOME=$(/usr/libexec/java_home -v 1.8)

echo "✅ Switched to Java 8"
echo ""
echo "Current Java version:"
java -version
echo ""
echo "JAVA_HOME is set to: $JAVA_HOME"
echo ""
echo "This change is temporary for this terminal session."
echo "To make it permanent, add this to your ~/.zshrc:"
echo ""
echo "  export JAVA_HOME=\$(/usr/libexec/java_home -v 1.8)"
echo ""
echo "=================================================="
echo ""
echo "You can now run Malmo/Minecraft:"
echo "  cd ../malmo/Minecraft"
echo "  ./launchClient.sh"
echo ""
