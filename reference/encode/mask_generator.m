f=fopen('mask.txt','w');
for i=1:49
    for j=1:97
        fprintf(f,'%i\t',random('unid',3)-1);
    end
    fprintf(f,'\r\n');
end
fclose(f);