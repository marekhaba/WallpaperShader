#version 430 core

#define DECAY vec4(0.01,0.01,0.01,0.0)
#define DIFFUSE vec4(0.9,0.9,0.9,1.0)

layout (local_size_x = 32, local_size_y = 32) in;

layout (binding = 0, rgba8) readonly uniform image2D img_input;
layout (binding = 1, rgba8) writeonly uniform image2D img_output;

void main(void)
{
    ivec2 IMAGE_SIZE = imageSize(img_input);

    //vec4 texel;
    ivec2 pos = ivec2(gl_GlobalInvocationID.xy);

    if (pos.x > IMAGE_SIZE.x || pos.x < 0 || pos.y > IMAGE_SIZE.y || pos.y < 0){
        return;
    }

    vec4 og_color = imageLoad(img_input,pos);

    vec4 color_sum = imageLoad(img_input,pos);
    color_sum +=  imageLoad(img_input,pos+ivec2(-1,-1));
    color_sum +=  imageLoad(img_input,pos+ivec2(-1, 0));
    color_sum +=  imageLoad(img_input,pos+ivec2(-1, 1));
    color_sum +=  imageLoad(img_input,pos+ivec2( 0,-1));
    color_sum +=  imageLoad(img_input,pos+ivec2( 0, 1));
    color_sum +=  imageLoad(img_input,pos+ivec2( 1,-1));
    color_sum +=  imageLoad(img_input,pos+ivec2( 1, 0));
    color_sum +=  imageLoad(img_input,pos+ivec2( 1, 1));

    vec4 blured_color = (color_sum/9.0);
    vec4 color;
    color = mix(og_color, blured_color, DIFFUSE);


    imageStore(img_output, pos, vec4(clamp(color-DECAY,0.0,1.0)));
    //imageStore(img_output, pos, og_color);
    //barrier();
    //memoryBarrierShared();
}