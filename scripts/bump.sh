#!/usr/bin/env sh

# Replace latest tag by the bumped version in action.yml
echo "Updating references in action and README (main ➡ ${CZ_PRE_NEW_VERSION})" >&2
sed -i "s/main/${CZ_PRE_NEW_VERSION}/g" action.yml
sed -i "s/main/${CZ_PRE_NEW_VERSION}/g" README.md
