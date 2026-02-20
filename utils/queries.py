sql_stages_podium = """
SELECT 
t.stage_id,
t.stage_name as stage,
t.stage_date as date,
t.stage_1 as "1st Stage",
t.stage_2 as "2nd Stage",
t.stage_3 as "3rd Stage",
t.race_1  as "1st GC",
t.race_2  as "2nd GC",
t.race_3  as "3rd GC"
FROM v_stage_podium t WHERE race_id = ?
--and stage_date <= date('now')
""" 

sql_next_stages = """
select race_id, stage_id, stage_name, stage_date from stages where race_id = (
SELECT 
 s.race_id
FROM stages s
where s.stage_id = ?
    )
"""

sql_races = """
SELECT * FROM races where race_id = ?
"""

sql_stages_chart = """
SELECT 
 t.race_name,
 t.stage_number,
 t.stage_name,
 t.team_manager,
 t.cum_pts
FROM v_stage_points t
where race_id = ?
and   results_ready = 1
and stage_date <= date('now')
"""

sql_stage_results = """
        SELECT 
        t.results_ready,
        t.team_id,
        t.race_name,
        t.stage_name,
        t.stage_date,
        t.stage_rank as "No.",
        t.team_name "Team", 
        --t.team_manager "Manager",
        case when t.team_manager = 'Simis' then 'Baba Vanga' else t.team_manager end as "Manager", 
        t.pts "Stage points"
        FROM v_stage_points t
        where t.stage_id = ?
        order by t.pts desc
"""

sql_gc_results = """
        SELECT 
        t.results_ready,
        t.team_id,
        t.race_name,
        t.stage_name,
        t.stage_date,
        case when t.results_ready = 0 then 1 else t.race_rank end as "No.",
        t.team_name "Team", 
        --t.team_manager "Manager", 
        case when t.team_manager = 'Simis' then 'Baba Vanga' else t.team_manager end as "Manager", 
        case when t.results_ready = 0 then null else t.cum_pts end as "GC points"
        FROM v_stage_points t
        where t.stage_id = ?
        order by t.cum_pts desc
"""

sql_stage_roster ="""
    SELECT t.team_manager, t.rider, t.total, t.cost
    FROM v_stage_roster t
    WHERE stage_id = ?
    --and   rider is not null -- remove later, bcs Shaun joined late
    order by t.team_manager, t.total desc
"""

sql_calendar = """
SELECT 
 s.stage_id,
 case when s.stage_date between date('now') and datetime('now','+3 days') then 1 else 0 end as warning,
 r.name as 'Race',
 s.stage_name as 'Stage',
 date(s.stage_date) as 'Date',
 --time(s.stage_date) as 'Cut-Off time',
 ifnull(sp.stage_1,'') as 'Stage winner',
 ifnull(sp.race_1,'') as 'GC Leader'
FROM races r
join stages s
    on s.race_id = r.race_id
left join v_stage_podium sp
    on sp.stage_id = s.stage_id
where 0=0 
and s.stage_date between date('now','-3 days') and date('now','+3 days')
and not (s.stage_number != 22 and r.race_id = 2)
order by s.stage_date
"""

sql_stage ="""
SELECT 
 r.name as race_name,
 s.stage_name,
 s.stage_date
FROM stages s
join races r
    on r.race_id = s.race_id
where 0=0
and   s.stage_id = ?
"""

sql_riders_rank="""
with prep as (
select 
 t.race_id, 
 t.rider_code,
 sum(t.points) points 
from stage_points t
group by 
 t.race_id,
 t.rider_code
      )
, selections as (
select 
 t.race_id,
 t.rider_code,
 count(distinct t.team_id) as selections 
from v_stage_roster t
group by 
 t.race_id,
 t.rider_code
        )      
select 
 rc.race_id, 
 rc.name as race_name,
 r.rider_code,
 r.name "Rider",
 r.team,
 ifnull(s.selections,0) "Picks",
 r.cost "Cost",
 ifnull(p.points,0) "Points",
 ifnull(p.points/r.cost,0) "Points/Cost"
from riders r
join races rc
 on rc.race_id = r.race_id
left join prep p
 on p.race_id = rc.race_id
 and p.rider_code = r.rider_code
left join selections s
 on s.race_id = r.race_id
 and s.rider_code = r.rider_code
where rc.race_id = ?
order by r.cost desc 
"""

sql_riders_rank_old="""
SELECT 
  t.race_id,
  t.race_name,
  t.rider_code,
  t.rider "Rider",
  t.team,
  min(t.cost)*1. as "Cost",
  count(*) as "Selections", 
  count(distinct t.stage_id)*1. as "Starts",
  sum(t.total)/count(distinct t.team_manager)*1.  as "Points",
  sum(t.total*1.)/count(distinct t.team_manager)/min(t.cost) as "Points/Cost",
  sum(t.total*1.)/count(distinct t.team_manager)/count(distinct t.stage_id) as "Points/Start"
FROM v_stage_roster t
where 0=0
and   race_id = ?
and   stage_date <= date('now')
group by 
 t.rider, t.rider_code, t.race_name, t.rider_code
order by min(t.cost*1.) desc
"""

sql_riders_rank_all="""
SELECT 
  t.race_id,
  t.race_name,
  t.rider_code,
  t.rider "Rider",
  t.team,
  min(t.cost)*1. as "Cost",
  count(*) as "Selections", 
  count(distinct t.stage_id)*1. as "Starts",
  sum(t.total)/count(distinct t.team_manager)*1.  as "Points",
  sum(t.total*1.)/count(distinct t.team_manager)/min(t.cost) as "Points/Cost",
  sum(t.total*1.)/count(distinct t.team_manager)/count(distinct t.stage_id) as "Points/Start"
FROM v_stage_roster t
join races r
    on r.race_id = t.race_id
    and r.year = 2026
    and r.race_id != 96
where 0=0
and   stage_date <= date('now')
--and   race_id = ?
group by 
 t.rider, t.rider_code, t.race_name, t.rider_code
order by min(t.cost*1.) desc
"""

sql_rider="""
with prep as (
    SELECT 
     rank() over (partition by t.stage_id, t.race_id order by random()) rank,
     case when sum(ifnull(t.total,0)) over (partition by t.race_id, t.stage_number) = 0 then 0 else 1 end as results_ready,
     t.*
    FROM v_stage_roster t
    where 0=0
    and   race_id = ?
    and   t.rider_code = ?
        )
SELECT 
 race_id,
 rider_code,
 rider,
 stage_name as "Stage name",
 date(stage_date) "Date",
 team as "Team",
 cost as "Cost",
 total  as "Points",
 total*1/cost  as "Points/Cost"
FROM prep  
where rank = 1
and results_ready = 1

"""

sql_teams="""
select 
 t.team_id,
 t.race_name,
 rank() over (partition by race_id order by t.cumulative_pts desc) as "Position",
 t.team_name as "Team",
 t.team_manager as "Manager",
 t.stage_number||'-'||t.stage_name as "Last stage",
 t.cumulative_pts as "Points",
 -1*t.race_gap as "Gap",
 t.wins as "Stage wins"
from (
    select 
     t.*,
     sum(case when stage_rank = 1 then 1 else 0 end) over (partition by race_id, team_id) as wins,
     dense_rank() over (partition by race_id order by stage_number desc) stg_rev_rnk
     from v_stage_results_detail t 
     where race_id = ?
             ) t
where stg_rev_rnk = 1
order by 2
"""

sql_teams_chart = """
     select 
      t.race_name,
      t.stage_number,
      t.stage_name,
      t.team_manager,
      -t.race_gap as cum_pts
     from v_stage_results_detail t
     where race_id = ?
"""

sql_team = """
    select 
     t.race_name,
     t.team_name,
     t.team_manager,
     t.stage_number,
     t.stage_name,
     t.stage_rank,     
     t.pts,
     t.stage_gap,
     
     t.cumulative_pts,     
     t.race_gap
     
     from v_stage_results_detail t 
     where 0=0
     and   team_id = ?
     order by t.stage_number
"""

sql_team_detail = """
select 
 t.rider,
 t.team,
 t.cost,
 t.stage_number,
 t.stage_name,
 sum(t.total) as pts
from v_stage_roster t
where t.team_id = ?
group by
 t.rider,
 t.team,
 t.cost,
 t.stage_number,
 t.stage_name
"""

sql_races_podium_year="""
select 
 t.race_name, 
 t.race_1 "1st",
 t.race_2 "2nd",
 t.race_3 "3rd" 
from v_stage_podium t
join races r
    on t.race_id = r.race_id
    and r.year = 2026
where 0=0
and   stage_number = 22
--and   race_1 != '-'
order by t.race_id desc 
"""

sql_teams_overall = """
select 
 rank() over (order by sum(pts) desc) Position,
 t.team_manager "Manager",
 sum(pts) as "Points",
-- sum(stage_gap) as "Gap",
 sum(case when stage_rank = 1 then 1 else 0 end) as "Wins count"
 from v_stage_results_detail t 
where 0=0
group by 
 --t.team_name,
 t.team_manager
order by sum(pts) desc
"""

sql_teams_overall_year = """
select 
 t.team_code,
 rank() over (order by sum(pts) desc) Position,
 t.team_manager "Manager",
 sum(pts) as "Points",
-- sum(stage_gap) as "Gap",
 sum(case when stage_rank = 1 then 1 else 0 end) as "Wins count"
 from v_stage_results_detail t 
where 0=0
and   t.year = 2026
and   t.race_id != 96
group by 
 --t.team_name,
 t.team_manager
order by sum(pts) desc
"""

sql_navbar = """
SELECT 
    name || '-' || substr(year, -2) AS display_name, 
    race_id,
    year,
    CASE 
        WHEN ROW_NUMBER() OVER (ORDER BY end_date DESC) <= 5 THEN 1 
        ELSE 0 
    END AS is_active
FROM races 
ORDER BY end_date DESC;
"""

sql_team_history="""
WITH prep AS (
    SELECT 
        t.race_id,
        t.race_name,
        t.team_id,
        t.team_code,
        MAX(t.team_name) AS team_name,
        max(t.team_manager) team_manager,
        SUM(t.pts) AS pts,
        CASE 
            WHEN DATE('now') BETWEEN r.start_date AND r.end_date THEN 1 
            ELSE 0 
        END AS current_race
    FROM v_stage_points t
    JOIN races r ON r.race_id = t.race_id
    WHERE r.year = '2026'
    and   r.race_id != 96
    GROUP BY t.race_id, t.race_name, t.team_code
)
, fin as (
SELECT 
    *,
    -- 1. Rank of team within each race
    RANK() OVER (
        PARTITION BY race_id 
        ORDER BY pts DESC
    ) AS race_rank,
    -- 2. Gap to the best team in the race
    (MAX(pts) OVER (PARTITION BY race_id) - pts) AS gap_to_leader,
    DENSE_RANK() OVER (
            ORDER BY race_id ASC
        ) AS season_race_number,
    SUM(pts) OVER (
            PARTITION BY team_code 
            ORDER BY race_id 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_pts
FROM prep
ORDER BY race_id DESC, race_rank ASC
    )
select 
 t.race_id,
 t.team_id,
 t.team_code,
 t.current_race,
 t.team_name "Team",
 t.team_manager "Manager",
 t.season_race_number "No",
 t.race_name "Race",
 t.pts "Score",
 t.race_rank "GC result",
 t.gap_to_leader "GC gap",
 t.cumulative_pts as "Season points"
from fin t
where t.team_code = ?
order by race_id 
"""

sql_report = """
select  
 s.stage_category,
 t.team_name,
 t.team_manager,
 count(*) as days_in_lead
from v_stage_points t
join stages s
	on s.stage_id = t.stage_id
where t.race_id = 2
and   t.stage_rank = 1
and	  s.stage_category = 3
group by 
 s.stage_category,
 t.team_name,
 t.team_manager
 order by 4 desc
"""