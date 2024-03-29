# Load environment variables from .env file
ifneq (,$(wildcard ./.env))
    include .env
    export
endif


all:
	@echo network-routing makefile options include:
	@echo -----------------------------------------
	@echo - prepare-initial-database
	@echo - prepare-for-analysis
	@echo - sidewalk-gaps-map
	@echo - database-backup


prepare-initial-database:
	db build-initial


prepare-for-analysis:
	db build-secondary 1
	db build-secondary 2
	db build-secondary 3
	db build-secondary 4
	db build-secondary 5
	db build-secondary 6
	db build-secondary 7
	db build-secondary 8
	db build-secondary 9
	db build-secondary 10
	db build-secondary 11
	db build-secondary 12
	db build-secondary 13
	db build-secondary 14
	db make-nodes-for-edges osm_edges_all_no_motorway
	db make-nodes-for-edges pedestriannetwork_lines
	db make-nodes-for-edges lowstress_islands


sidewalk-gaps-map:
	gaps classify-osm-sw-coverage
	gaps scrub-osm-tags
	gaps identify-islands
	access sw-default
	access eta-schools
	db export-geojson gaps

	access sw-access-score
	access osm-access-score
	gaps isochrones-accessscore
	db export-geojson accessscore

	db make-vector-tiles gaps sidewalk_gap_analysis


rrmp:
	access rrmp-sw
	access rrmp-lts
	gaps isochrones-rrmp
	db export-geojson rrmp


database-backup:
	${PG_DUMP_PATH} ${DATABASE_URL} > network_routing_backup.sql
