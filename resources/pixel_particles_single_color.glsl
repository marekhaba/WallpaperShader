#version 430 core

#define PI 3.14159265359

#define PULL 0.5 // pull toward original position
#define PUSH 1.0 // push away from the mouse
#define CLOSE_TRESHOLD 1.0 // How close point need to be to think they are in a right spot
#define DRAG 0.99

layout (local_size_x = 16, local_size_y = 1) in;

layout (binding = 1, rgba8) readonly uniform image2D img_input;//needs to be the opposite than in diffuse
layout (binding = 0, rgba8) writeonly uniform image2D img_output;

uniform float agents_count;

struct Agent
{
    vec2 position;
    float angle;
    float padding;
    vec2 velocity;
    vec2 original_postion;
};

layout (std430, binding = 2) buffer AgentsBlock
{
    Agent agents[];
} input_data;

layout (binding = 3, rgba8) readonly uniform image2D mask;

uniform vec2 mouse;
uniform vec2 delta_mouse;



float random(float x){ //mby get better random
    return fract(sin(x)*100000.0);
}

//https://stackoverflow.com/questions/4200224/random-noise-functions-for-glsl
float random(vec2 co){
    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

float angle_to_point(vec2 point, vec2 pos){
    return atan(point.y-pos.y, point.x-pos.x);
}

float distance_line(vec2 line_P1, vec2 line_P2, vec2 point){
    return abs( (line_P2[0]-line_P1[0])*(line_P1[1]-point[1]) - (line_P1[0]-point[0])*(line_P2[1]-line_P1[1]) ) / sqrt(pow(line_P2[0]-line_P1[0],2) + pow(line_P2[1]-line_P1[1],2) );
}

void main()
{
    //Constants
    vec2 IMAGE_SIZE = vec2(imageSize(img_input));
    //float force_treshold = 0.1; // How large the dorce has to be to have any effect

    //Do not execute if there are no more agents
    //Easy workaround around having to be precise with job count
    uint i = gl_GlobalInvocationID.x;
    if (i > agents_count){
        return;
    }

    vec2 pos = input_data.agents[i].position;
    float angle = input_data.agents[i].angle;
    vec2 velocity = input_data.agents[i].velocity;

    angle = angle_to_point(mouse, pos);
    float distance_mouse = distance_line(mouse, mouse-delta_mouse, pos);
    vec2 force = delta_mouse/max(distance_mouse, 1.0);
    //if (abs(force[0])+abs(force[1]) > force_treshold){
    velocity += force*PUSH;//vec2(cos(-angle), sin(-angle))*force;
    //}
    //pull
    float distance_original = distance(input_data.agents[i].original_postion, pos);
    if (distance_original > CLOSE_TRESHOLD){
        angle = angle_to_point(input_data.agents[i].original_postion, pos);
        velocity += vec2(cos(angle), sin(angle))*PULL;
    }
    

    velocity *= DRAG;

    vec2 newpos = pos+velocity;

    if (newpos.x>IMAGE_SIZE.x || newpos.x<0 || newpos.y>IMAGE_SIZE.y || newpos.y<0){
        newpos.x = min(IMAGE_SIZE.x-0.001,max(newpos.x-0.001, 0.0));
        newpos.y = min(IMAGE_SIZE.y-0.001,max(newpos.y-0.001, 0.0));
    }
    else
    {
        vec4 prev_val = imageLoad(img_input, ivec2(newpos));
        imageStore(img_output, ivec2(newpos), prev_val+vec4(0.01*distance_original/10, 0.0175, 0.205, 1.0)*2.75);
        //imageStore(img_output, ivec2(newpos), vec4(0.8549, 0.398, 0.6745, 1.0)*0.5);
    }
    input_data.agents[i].position = newpos;
    input_data.agents[i].velocity = velocity;

}