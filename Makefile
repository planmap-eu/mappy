VERSION=$(shell git describe --tags --abbrev=0)

qgismappy:
	cp -r qgis_plugin/qgismappy qgismappy

qgismappy/mappy:
	cp -r mappy qgismappy/
	
clean:
	rm -fr qgismappy
	rm -fr qgismappy_*.zip
	
package: qgismappy qgismappy/mappy
	$(info    VERSION:  $(VERSION))
	zip -qq qgismappy_$(VERSION).zip -r qgismappy
	

	
