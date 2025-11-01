#!/bin/bash
set -e

echo "🔍 Validating Frontend Build..."
echo ""

# Check Node.js version
echo "📦 Checking Node.js version..."
node_version=$(node -v)
echo "   Node.js: $node_version"
if [[ ! "$node_version" =~ ^v(18|19|20|21|22) ]]; then
  echo "   ⚠️  Warning: Node.js 18+ recommended"
fi
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo "📥 Installing dependencies..."
  npm install
  echo ""
fi

# Run TypeScript check
echo "🔧 Running TypeScript check..."
npm run build -- --mode development || {
  echo "❌ TypeScript check failed"
  exit 1
}
echo "✅ TypeScript check passed"
echo ""

# Check for lint errors
echo "🔍 Checking code style..."
npm run lint || {
  echo "⚠️  Linting found issues (non-blocking)"
}
echo ""

# Build for production
echo "🏗️  Building for production..."
rm -rf dist
npm run build || {
  echo "❌ Production build failed"
  exit 1
}
echo "✅ Production build successful"
echo ""

# Check build artifacts
echo "📊 Build artifacts:"
du -sh dist
echo ""
echo "Files:"
find dist -type f -name "*.js" -o -name "*.css" -o -name "*.html" | sort
echo ""

# Check for large files
echo "🔍 Checking for large files (>500KB)..."
large_files=$(find dist -type f -size +500k)
if [ -n "$large_files" ]; then
  echo "⚠️  Large files detected:"
  echo "$large_files" | while read -r file; do
    size=$(du -h "$file" | cut -f1)
    echo "   - $file ($size)"
  done
  echo "   Consider code splitting or optimization"
else
  echo "✅ No large files found"
fi
echo ""

# Validate environment files
echo "🔍 Checking environment configuration..."
if [ -f ".env.example" ]; then
  echo "✅ .env.example found"
else
  echo "⚠️  .env.example not found"
fi

if [ -f ".env.development" ]; then
  echo "✅ .env.development found"
else
  echo "⚠️  .env.development not found"
fi
echo ""

# Check critical files
echo "🔍 Validating critical files..."
critical_files=(
  "dist/index.html"
  "dist/assets/index.css"
)

all_found=true
for file in "${critical_files[@]}"; do
  if [ ! -f "$file" ]; then
    echo "❌ Missing: $file"
    all_found=false
  fi
done

if [ "$all_found" = true ]; then
  echo "✅ All critical files present"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Validation Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Start development server: npm run dev"
echo "  2. Preview production build: npm run preview"
echo "  3. Deploy dist/ folder to your hosting platform"
echo ""
