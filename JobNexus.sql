create database JobNexus;
use  JobNexus;

create table job_seeker(
js_id int auto_increment primary key,
js_email varchar(100) not null unique, -- email provided for login
-- bcrypt hashes are 60 chars
js_password CHAR(255) NOT NULL);


create table js_operation(
js_id int not null,
oper_id int auto_increment primary key,
js_name varchar(255),
resume_path varchar(255), -- path of resume that is stored in uploads file in directory
resume_score int,
job_role varchar(50) ,-- predicted by llm by processing resume
permission bool not null default 0,
contact_email varchar(100),
skills varchar(1000),
FOREIGN KEY (js_id) REFERENCES job_seeker(js_id)ON DELETE CASCADE ON UPDATE CASCADE);


create table missing_skills(
ms_id int auto_increment primary key,
oper_id int not null,
missing_skill varchar(100) not null,
FOREIGN KEY (oper_id) REFERENCES js_operation(oper_id)ON DELETE CASCADE ON UPDATE CASCADE);


create table recommended_courses(
ms_id int not null,
course_link varchar(100) not null,
primary key(ms_id,course_link),
FOREIGN KEY (ms_id ) REFERENCES missing_skills(ms_id )ON DELETE CASCADE ON UPDATE CASCADE);


create table recruiter(
recruiter_id int auto_increment primary key,
recruiter_email varchar(100) not null unique,
recruiter_password CHAR(255) NOT NULL);


create table recruiter_uploads(
resume_id int auto_increment primary key,
recruiter_id int,
candidate_name VARCHAR(100),
resume_path varchar(255), -- path of resume that is stored in uploads file in directory
resume_score int,
job_role varchar(50),
contact_email varchar(100),
mat_skill_str varchar(1000),
foreign key(recruiter_id) references recruiter(recruiter_id) on delete cascade on update cascade);


select * from job_seeker;
select * from js_operation;
select * from missing_skills;
select * from recommended_courses;
select * from recruiter;
select * from recruiter_uploads;
