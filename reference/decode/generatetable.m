P=imread('Final.jpg');
P=rgb2hsv(P);
ref=zeros(1,16);
for i=1:16
    x=i*32-16;
    y=16;
    ref(i)=P(x,y,1)*360;
end
hue=zeros(59,33);
table=zeros(59,33);
for i=1:59
    for j=1:33
        x=i*16-8;
        y=j*16+56;
        hue(i,j)=P(x,y,1)*360;
        for k=1:16
            if (hue(i,j)>ref(k) && hue(i,j)<ref(mod(k,16)+1)) || (ref(k)-ref(mod(k,16)+1)>180 && ((hue(i,j)>ref(k) || hue(i,j)<ref(mod(k,16)+1))))
                table(i,j)=k;
                break;
            end
        end
    end
end