VERSION=$(shell git describe --tags --abbrev=0)

qgismappy:
	cp -r qgis_plugin/qgismappy qgismappy

qgismappy/mappy:
	cp -r mappy qgismappy/
	
clean:
	rm -fr qgismappy
	rm -fr qgismappy-*.zip
	
updateversion:
	sed -i  's/version=[.0-9]*/version=$(VERSION)/g' qgis_plugin/qgismappy/metadata.txt 
	
package: updateversion qgismappy qgismappy/mappy
	$(info    VERSION:  $(VERSION))
	zip -qq qgismappy-$(VERSION).zip -r qgismappy
	rm -fr qgismappy
	
	

	
