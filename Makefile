qgismappy:
	cp -r qgis_plugin/qgismappy qgismappy

qgismappy/mappy:
	cp -r mappy qgismappy/
	
clean:
	rm -fr qgismappy
	
package: qgismappy qgismappy/mappy
	TAG=$(git tag --points-at HEAD)
	echo "compressing version" $TAG

	zip -qq qgismappy_$TAG.zip -r qgismappy
