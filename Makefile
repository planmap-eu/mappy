VERSION=$(shell git describe --tags --abbrev=0)

qgismappy:
	cp -r qgis_plugin/qgismappy qgismappy

qgismappy/mappy:
	cp -r mappy qgismappy/
	
clean:
	rm -fr qgismappy
	rm -fr qgismappy-*.zip
	
package: qgismappy qgismappy/mappy
	$(info    VERSION:  $(VERSION))
	zip -qq qgismappy-$(VERSION).zip -r qgismappy
	

	
