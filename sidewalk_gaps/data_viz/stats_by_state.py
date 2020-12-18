query = """
select state, osm_hwy_clean,
    sum(len_meters) as total, 
    sum(case when sw_ratio > 0.82 then len_meters else 0 end) * 0.000621371 as have_full_sw,
    sum(case when sw_ratio <= 0.82 and sw_ratio > 0.45 then len_meters else 0 end) * 0.000621371 as partial_sw,
    sum(case when sw_ratio <= 0.45 then len_meters else 0 end) * 0.000621371 as need_full_sw
from data_viz.osm_sw_coverage osc
where st_within(st_centroid(geom), (select st_collect(geom) from regional_counties rc))
group by state, osm_hwy_clean
order by osm_hwy_clean, state

"""
