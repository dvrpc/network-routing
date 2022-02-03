
all:
	@echo network-routing makefile options include:
	@echo -----------------------------------------
	@echo - prepare-initial-database
	@echo - prepare-for-analysis


prepare-initial-database:
	db build-initial

prepare-for-analysis:
	db build-secondary 2
	db build-secondary 3
	db build-secondary 4
	db build-secondary 5
	db build-secondary 6
	db build-secondary 7
	db build-secondary 8
	db build-secondary 9
	db make-nodes-for-edges osm_edges_all_no_motorway
	db make-nodes-for-edges pedestriannetwork_lines
	db make-nodes-for-edges lowstress_islands
