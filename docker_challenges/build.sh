#!/bin/bash
# Build script for CTFArena Docker challenges
set -e

echo "========================================="
echo " CTFArena - Building Docker Challenges"
echo "========================================="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "[1/2] Building sqli-lab..."
docker build -t ctfarena/sqli-lab:latest "$SCRIPT_DIR/sqli-lab"
echo "  ✓ sqli-lab built successfully"

echo ""
echo "[2/2] Building privesc..."
docker build -t ctfarena/privesc:latest "$SCRIPT_DIR/privesc"
echo "  ✓ privesc built successfully"

echo ""
echo "========================================="
echo " All challenges built successfully!"
echo "========================================="
echo ""
echo "Images:"
docker images --filter "reference=ctfarena/*" --format "  {{.Repository}}:{{.Tag}} ({{.Size}})"
