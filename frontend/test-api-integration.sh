#!/bin/bash
set -e

API_BASE="${1:-http://localhost:8000/api/v1}"

echo "🧪 Testing API Integration"
echo "API Base URL: $API_BASE"
echo ""

# Test 1: Health Check
echo "1️⃣  Testing health endpoint..."
response=$(curl -s -w "\n%{http_code}" "${API_BASE}/health")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
  echo "✅ Health check passed"
  echo "   Response: $body"
else
  echo "❌ Health check failed (HTTP $http_code)"
  echo "   Response: $body"
  exit 1
fi
echo ""

# Test 2: List Languages
echo "2️⃣  Testing languages endpoint..."
response=$(curl -s -w "\n%{http_code}" "${API_BASE}/languages")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
  echo "✅ Languages endpoint working"
  lang_count=$(echo "$body" | grep -o '"code"' | wc -l | tr -d ' ')
  echo "   Found $lang_count languages"
else
  echo "❌ Languages endpoint failed (HTTP $http_code)"
  echo "   Response: $body"
  exit 1
fi
echo ""

# Test 3: List Voices
echo "3️⃣  Testing voices endpoint..."
response=$(curl -s -w "\n%{http_code}" "${API_BASE}/voices")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
  echo "✅ Voices endpoint working"
  voice_count=$(echo "$body" | grep -o '"name"' | wc -l | tr -d ' ')
  echo "   Found $voice_count voices"
else
  echo "❌ Voices endpoint failed (HTTP $http_code)"
  echo "   Response: $body"
  exit 1
fi
echo ""

# Test 4: List Jobs
echo "4️⃣  Testing jobs list endpoint..."
response=$(curl -s -w "\n%{http_code}" "${API_BASE}/jobs?user_id=default_user&page=1&page_size=10")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
  echo "✅ Jobs list endpoint working"
  job_count=$(echo "$body" | grep -o '"job_id"' | wc -l | tr -d ' ')
  echo "   Found $job_count jobs"
else
  echo "❌ Jobs list endpoint failed (HTTP $http_code)"
  echo "   Response: $body"
  exit 1
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ All API Integration Tests Passed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "API endpoints tested:"
echo "  ✓ GET /health"
echo "  ✓ GET /languages"
echo "  ✓ GET /voices"
echo "  ✓ GET /jobs"
echo ""
echo "Frontend is ready to connect to the backend!"
echo ""
