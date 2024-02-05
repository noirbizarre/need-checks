#!/usr/bin/env sh

VERSION=${CZ_POST_CURRENT_VERSION}

# Create or update MAJOR and MAJOR.MINOR tags
MAJOR_MINOR=${VERSION%.*}
echo "Tagging <major>.<minor> version v${MAJOR_MINOR}"
git tag -fa "v${MAJOR_MINOR}" -m "Update major.minor version tag"
git push origin "v${MAJOR_MINOR}" --force

MAJOR=${VERSION%%.*}
echo "Tagging <major> version v${MAJOR}"
git tag -fa "v${MAJOR}" -m "Update major version tag"
git push origin "v${MAJOR}" --force


# Prepare next dev version
echo "Prepare next development cycle"
sed -i "s/${VERSION}/main/g" action.yml
git commit -am "build: prepare next \`main\` version"
git push
