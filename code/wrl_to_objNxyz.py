import os
import json
import re
import copy

def wrl_to_xyz(wrl_input_path : str, obj_form_path : str ,obj_output_path : str,
               xyz_output_path : str, label_num_path : str, input_wrl_file : str
               , big_err_range : str, obj_mode : str):

    big_err_range = int(big_err_range)
    wrl_input_path = wrl_input_path
    obj_form_path = obj_form_path
    obj_output_path = obj_output_path
    xyz_output_path = xyz_output_path
    label_num_path = label_num_path
    input_wrl_file = input_wrl_file
    # with open(stl_input_path, "r") as STL: # stl_input_path 파일을 한행씩으로 요소로 같은 리스트로 담는다.
    #     stl_lines = STL.readlines()
    ########## rgb 값별 매칭되는 라벨넘버를 읽어오는 객체 ###############################################################
    with open(label_num_path, "r") as f: # json 파일을 열러서 "라벨넘버": "r g b" 로 구성된 딕셔너리를 읽어온다.
        color_idx_dict: dict = json.load(f)
    color_idx_key_v = color_idx_dict.items() # [('점의 class 넘버가 key' ,'점의 rgb 값을 value 값'), (...)] 형태의
                                             # 리스트
    rgb_atom_list = [] # rgb요소들 중에 중복을 제외한 요소들을 담을 리스트, 정의되지 않은 rgb요소값을 제거하기 위함.
    for ciky in color_idx_key_v:
        k = ciky[0]
        vl = ciky[1]
        vl = vl.split(" ") # rgb를 r,b,g로 분해
        for v in vl:
            rgb_atom_list.append(v)
    rgb_atom_list = list(set(rgb_atom_list)) # rgb요소들 중에 중복을 제외한 요소들 리스트.



    # 정답파일을 읽어서 객체에 담는다. 이를 input인 obj와 label인 xyz로 전처리하여 출력한다.
    with open(wrl_input_path, 'r') as F:
        origin = F.read()
    # 정답파일을 "{}"기준으로 구분하는데 그러면 2개의 요소를 가진 리스트로 구분되고 여기서 두번째 요소가 색체정보임
    # parsing = re.findall('\{([^}]+)', origin)   # 이게 작동함 포인트랑 색체 2로 구분함.
    parsing = re.findall('{([^}]+)', origin)  # 이렇게 하면 전체에서 {가 시작되고 }를 만나는 부분까지 분리해서 추출하는 듯.
                                              # (점좌표값 및 기타)와 (rgb 및 기타)로 나뉜다.

    print (parsing)
    print("parsing으로 나누어진 리스트 수: ",len(parsing))
    parsing_idx = origin.split("coordIndex ") # coordIndex 기준으로 문서내용을 나누면 대략
                                              # (점좌표값 및 기타)와 (셀,rgb및 기타)으로 나뉜다.
    parsing01 = parsing[0] # (점좌표값 및 기타)
    parsing02 = parsing[1] # (rgb 및 기타)
    print("parsing01:", parsing01)
    print("parsing02:", parsing02)
    print("parsing01_type:", type(parsing01))
    print("parsing02_type:", type(parsing02))

    # parsing 으로 인해 2개로 나줘진 리스트의 첫번째 리스트는 Crown Polygon의 point좌표값이 포함되어 있어야 하고
    # 두번째 리스트에는 각 point 좌표값(x,y,z)에 대응하는 color값이 매칭되어 있다.
    coord = re.findall('\[([^]]+)', parsing01) # 정규식으로 첫번재리스트요소내의 '[]'안의 값인 crown polygon의 점좌표값 추출.
    color_rgb = re.findall('\[([^]]+)', parsing02) # 정규식으로 두번째리스으요소내에서 '[]'안의 값인 점좌표의 rgb 추출.
    coord_idx = re.findall('\[([^]]+)', parsing_idx[1]) # 정규식으로 해당리스트요소내에서 '[]'안의 값인 셀과 rgb정보 추출.
    coord_idx = coord_idx[0] # 셀정보 추출, (점인덱스 3개순서 정보임.)
    print("coord:", coord)
    print("color_rgb:", color_rgb)
    print("coord_idx:", coord_idx)

    # print("coord:", list(coord))
    # print("color_rgb:", list(color_rgb))

    print("coord_type:", type(coord))
    print("color_rgb_type:", type(color_rgb))
    print("coord_idx_type:", type(coord_idx))


    # for c,rgb in zip(coord, color_rgb): #
        # c_split = c.split(",")
    c_split = coord[0].split(",") # 점좌표를 ","단위로 나누면 한점씩 나눠진다.
    rgb_split = color_rgb[0].split(",") # 한점의 색체를 ","를 구분자로 나누면 rgb값으로 나눈다.
    coord_idx_split = coord_idx.split(",\n") # 셀정보를 하나의 셀정보(점1인덱스,점2인덱스, 점3인덱스)단위로 나뉜다.

    coord = [] # [ [x, y, z],[x, y, z], ...] 형태의 좌표리스트를 담을 리스트객체
    rgb  = [] # [[r, g, b],[r, g, b], ...] 형태의 rgb값(0 ~ 1) 리스트를 담을 리스트객체
    rgb_large = [] # 보통 [[r, g, b],[r, g, b], ... ]형태의 rgb값( 0 ~255) 리스트를 담을려고 했으나
                   # 오차제한을 넘어서는 r,g,b값들은 [[r,g],[r,b], ..]등으로 담기는 듯, 즉, 리스트요소수가 3개미만이면
                   # 해당 rgb리스트는 요소수가 3개미만이 되는 듯 한데 좀더 분석해볼 필요,
                   # 오차제한을 넘어서는 rgb 인덱스를 3개미만인 경우를 찾아 찾아낼수 있는듯.
    rgb_255form = [] # [[R, G, B], [,,], ...]형태의 0~255값의  요소들이 있음.

    rgb_255_small = []
    c_idx = [] # 한행마다 [1,2,3],.... 인덱스 리스트를 담은 리스트 객체
    # 점좌표리스트 [x y z] 를 스페이스바로 구분하여 나누어 [x, y, z] 로 구분해놓는다.
    for c_detail_split in c_split:
        c_detail_split = c_detail_split.split(" ")
        cood_small = [] # x, y, z 좌표값이 리스트요소로 들어간다.
        for c in c_detail_split:
            if ('' == c) or ('\n' == c): # 불필요해진 리스트요소들은 넘어간다.
                pass
            else: # 필요한 리스트 요소들만 객체에 담는다.
                cood_small.append(c) # ['18.637684', '-12.329448', '9.283658'] 형태로 z,y,z좌표값이 담긴 리스트
        coord.append(cood_small) # [['18.637684', '-12.329448', '9.283658'], [..,...,...,],.....]형태의 좌표값모음 리스트.


    rgb_dict = {} # [0:[150, 150, 100],1:[50, 150, 100],...] 형식으로 인덱스를 키,0~255로 변환된 rgb리스트를 벨류로 가짐.
    for n1, rgb_detail_split in enumerate(rgb_split): # 0~1사이의 값으로 된 r g b 외 여러 불필요한 정보가 포함된 리스트.
        rgb_detail_split = rgb_detail_split.split(" ") # " "인 스페이스바 단위로 str을 나눈다.
        rgb_small = [] # [50, 100, 100] 형태의 0~255사이의 값으로 된 rgb 리스트.
        rgb_small_float = [] # ['0.196078', '0.392157', '0.392157'] 형태의 0~255사이의 값으로 된 rgb 리스트.
        rgb_1in255 = [] # [50, 100, 100] 형태의 0~255사이의 값으로 된 rgb 리스트.인데 중복이라 필요한지 분석필요.
        err_rgb = {} # 오차제한을 넘어서는 경우 이렇게 해두는데 {298: 100}인뎃스를 키, 오파rgb를 벨류로 하는 딕셔너리인데
                     # 쓰이지는 않는것 같아서 일단 내버려 둠.
        for r in rgb_detail_split: # 불필요해진 리스트요소들은 넘어간다.
            if ('' == r) or ('\n' == r):
                pass
            else: # 필요한 리스트 요소들만 객체에 담는다.
                rgb_small_float.append(r) # float rgb 값 담음 .
                _r = round(float(r)*255) # 255FORMAT rgb 값으로 변환 후  담음 .
                # if (_r == 176) or (_r=='176'):
                #     temp ="sdfsd"
                ########## 오차범위내의 오차는 정상적인 r,g,b값으로 바꾸고 정상적인 r,g,b값은 정상 그대로 담는다.
                for rbg_atom in rgb_atom_list:
                    if 0 < abs(int(_r) - int(rbg_atom)) <= big_err_range:
                        _r = rbg_atom
                        rgb_small.append(int(_r))
                        # rgb_small.append(str(_r))
                    elif _r == int(rbg_atom):
                        rgb_small.append(_r)
                    # elif abs(int(_r) - int(rbg_atom)) >2 :
                    #     err_rgb.append(n)

                    else:
                        # rgb_small.append(_r)
                        err_rgb[n1] = _r #나중에 err_rgb 리스트객체가 아래어딘가코드에서 새로생김 확인필요.
                rgb_1in255.append(int(_r)) # 255form 의 [r,g,b] 형식으로 담음. 필요한 rgb만 0~255형태로 담음.
        rgb.append(rgb_small_float)
        # tme = 0
        # if rgb_small == [100]:
        #     tme += 1
        rgb_large.append(rgb_small) # 여기서 오차가 일정에러 이상이면 rgb_small의 요소수가 3개가 안됨.정상은 3개여야됨.

        rgb_255form.append(rgb_1in255) # 255form 의 [[r,g,b],[..]....] 이중 리스트로 담음.
        rgb_dict[n1] = rgb_1in255

    rgb_define_list = [] # 정의된 치아구분번호별 rgb 리스트
    for kv in color_idx_key_v: # 딕셔너리 item 객체에서 value 값만 리스트에 담기 위함.다음 단계에서  이리스트요소들을
        rgb_define_list.append(kv[1]) # 비교하기 위함.

    err_rgb = [] # 정의된 치아구분번호별 rgb리스트에 해당되지 않는 rgb를 추려냄.
    for n_rgb in rgb_dict.items():
        rgb_str = ' '.join(map(str, n_rgb[1]))
        if rgb_str not in rgb_define_list:
            err_rgb.append(n_rgb)
    err_rgb_copy = copy.deepcopy(err_rgb)

    correct_err_rgb = []
    for rgb_a in rgb_atom_list:
        for n1, err in enumerate(err_rgb):

            for n2, r_g_b in enumerate(err[1]):
                # _r_g_b = r_g_b[1]
                if str(r_g_b) == str(rgb_a):
                    continue
                elif 0 < abs(int(r_g_b) - int(rgb_a)) <= 2:
                    err_rgb_copy[n1][1][n2] = int(rgb_a)
                else:
                    correct_err_rgb.append(err)
                    
    # 정밀도문제를 포함한 에러에서 정밀도문제만 제거한 것을 객체에 담는다.이것이 문제가 되는 RGB값과 해당 인덱스이다.
    big_err = []
    for err_org in err_rgb:
        for err_copy in err_rgb_copy:
            if err_org == err_copy:
                big_err.append(err_copy)

    # big_err = set(err_rgb_copy)
    # temppp = set(correct_err_rgb)
                    # break

                ###### atom rgb 리스트를 먼전 for문에 돌리고 다음으로 실제 rgb리스트를 하위 for문으로 돌린 케이스
        #         for rbg_atom in rgb_atom_list:
        #
        #             if _r == int(rbg_atom):
        #                 rgb_small.append(_r)
        #                 break
        #
        #             elif 0 < abs(int(_r) - int(rbg_atom)) <= 2:
        #                 _r = rbg_atom
        #                 rgb_small.append(str(_r))
        #                 break
        #
        #             # elif abs(int(_r) - int(rbg_atom)) >2 :
        #             #     err_rgb.append(n)
        #
        #             else:
        #                 err_rgb[n] = _r
        #             #     pass
        #                 # err_rgb.append(_r)
        #
        # rgb.append(rgb_small_float)
        # rgb_large.append(rgb_small)
    # 폴리곤의 페이스를 나타낼때 인덱스로 표현되는데 필요없는 -1 을 제거하고 1부터시작하는 인덱스로 표현하기 위함.
    for cx_detail_split in coord_idx_split:
        cx_detail_split = cx_detail_split.strip()
        cx_detail_split = cx_detail_split.split(",")
        c_idx_small = []
        for cx in cx_detail_split:
            if int(cx) == -1:
                continue
            else:
                _cx = int(cx) + 1
                c_idx_small.append(_cx)
        c_idx.append(c_idx_small)

    # with open(lable_num_path, "r") as f: # json 파일을 열러서 "라벨넘버": "r g b" 로 구성된 딕셔너리를 읽어온다.
    #     color_idx_dict: dict = json.load(f)
    ###### obj 포맷 읽어오기.
    with open(obj_form_path, 'r') as obj_form:
        obj_line = obj_form.readlines()

    big_err_n = [] # 오차제한을 벗어나는 rgb값의 인덱스번호를 담는 객체.
    for nb in big_err:
        big_err_n.append(nb[0])

    ################### obj 파일을 결과물로 생성하는 코드 #########################################################
    with open(obj_output_path, 'w') as obj_exp:

        # obj_file_name = obj_line[5][:9] + input_wrl_file[:-4] + ".obj\n" # obj_line[5]와 바꿔치기 해야함.
        # vertices = obj_line[7][:-2] + str(len(coord)) + "\n" # obj_line[7]과 바꿔야 함.
        # faces = obj_line[8][:-2] + str(len(c_idx)) + "\n" # obj_line[8]과 바꿔야 함.

        # obj_line[5].replace(obj_line[5][:9], obj_line[5][:9] + input_wrl_file[:-4] + ".obj\n")
        # obj_line[7].replace(obj_line[7][:-2], obj_line[7][:-2] + str(len(coord)) + "\n")
        # obj_line[8].replace(obj_line[8][:-2], obj_line[8][:-2] + str(len(c_idx)) + "\n")
        # obj_line[15].replace(obj_line[15][2],str(len(coord)))# obj_line[15]과 바꿔야 함.
        # obj_line[19].replace(obj_line[19][2] ,str(len(c_idx)))# obj_line[19]과 바꿔야 함.
        obj_file_name = obj_line[5][:9] + input_wrl_file[:-4] + ".obj\n" # obj_line[5]와 바꿔치기 해야함.
        vertices = obj_line[7][:-2] + str(len(coord)) + "\n" # obj_line[7]과 바꿔야 함.
        faces = obj_line[8][:-2] + str(len(c_idx)) + "\n" # obj_line[8]과 바꿔야 함.
        vert_norm = obj_line[15].replace(obj_line[15][2],str(len(coord)))# obj_line[15]과 바꿔야 함.
        face_tex = obj_line[19].replace(obj_line[19][2] ,str(len(c_idx)))# obj_line[19]과 바꿔야 함.

        # obj_output_path 파일에 쓰여질 obj 메타정보.
        obj_line.remove(obj_line[5])
        obj_line.insert(5,obj_file_name)

        obj_line.remove(obj_line[7])
        obj_line.insert(7,vertices)

        obj_line.remove(obj_line[8])
        obj_line.insert(8,faces)

        obj_line.remove(obj_line[15])
        obj_line.insert(15,vert_norm)

        obj_line.remove(obj_line[19])
        obj_line.insert(19,face_tex)

        coord_str_join = []
        for cr in coord: # 좌표값 obj 포맷에 맞춰 바꾸기.
            cr[0] = "v " + cr[0]
            cr[2] = cr[2] + "\n"
            cr = ' '.join(cr)
            coord_str_join.append(cr)
        coordNrgb = []
        if (obj_mode == "all_zero") or (obj_mode == "err_zero") or (obj_mode == "real"):
            pass
        else:
            exit("obj_mode를 str타입의 all_zero , err_zero , real 중 하나로 입력하십시오.")

        for nn, (csj, rgb_elm) in enumerate(zip(coord_str_join, rgb)):
            # for rgb_elm in :
            # rgb_elm = ['0.000000', '0.000000', '0.000000'] ## obj의 rgb를 단색으로 할때 주석을 풀면 된다.RGB수치변환가능.
            if obj_mode == "all_zero":
                # cNr = csj[:-1] + " " + '0.000000' + " " + '0.000000' + " " + '0.000000' + "\n" # 검은색으로 표현
                cNr = csj[:-1] + " " + '1.000000' + " " + '1.000000' + " " + '1.000000' + "\n" # 흰색으로 표현

            ######## 큰 오차를 검은색으로 표현하는 코드 ###########################
            ######### 이는 오차를 눈으로 확인하는 용이고 제주한라대 보낼때는 위의 주석을 풀고 아래 if ,else 문을 주석처리한다.
            #########  즉, 제주한라대 보낼때는 rgb값을 0,0,0 즉 단색으로 보낸다.
            elif obj_mode == "err_zero":
                if nn in big_err_n:
                    cNr = csj[:-1] + " " + '0.000000' + " " + '0.000000' + " " + '0.000000' + "\n"
                else:
                    cNr = csj[:-1] +" " + rgb_elm[0] +" "+ rgb_elm[1] +" "+ rgb_elm[2] + "\n"

            elif obj_mode == "real":
                cNr = csj[:-1] + " " + rgb_elm[0] + " " + rgb_elm[1] + " " + rgb_elm[2] + "\n"

            coordNrgb.append(cNr)



        c_idx_str = []
        for c in c_idx: # 좌표 인덱스 값을 obj 포맷에 맞춰 바꾸기.
            c.insert(0,"f")
            c.insert(4,"\n")

            c[1] = str(c[1])
            c[2] = str(c[2])
            c[3] = str(c[3])
            c = ' '.join(c)
            c = c.replace(" \n", "\n")
            c_idx_str.append(c)

            # c.insert(-1, "f")
        obj_write_list = []
        obj_write01 = obj_line[:11]
        obj_write02 = coordNrgb
        obj_write03 = obj_line[15:17]
        obj_write04 = c_idx_str
        obj_write05 = obj_line[19:]

        obj_write_list.append(obj_write01)
        obj_write_list.append(obj_write02)
        obj_write_list.append(obj_write03)
        obj_write_list.append(obj_write04)
        obj_write_list.append(obj_write05)


        for obj_w in obj_write_list:
            for ob in obj_w:
                obj_exp.write(ob)


    # big_err_v = []
    # for n,err in enumerate(big_err):
    #     big_err_v.append(err[1])

    ##############  정답데이터 생성하는 코드 #######################################################################
    with open(xyz_output_path, 'w')as W: # 각 rgb 값에 대응되는 라벨넘버를 변환한다.

        # color_idx_itm = color_idx_dict.items() # dict_items([('1', '100 100 100'), ('2', '100 255 100'),.. 형식
        #
        # for k, v in color_idx_itm: #k= 치아구분넘버 str, v= RGB값 str
        #     for n, (cd, ix) in enumerate(zip(coord, rgb_large)): # 원래는 rgb 값만 넘기면 되는데 혹시나 둘다 넘기야 하는
        #
        #                                     # 상황을 대비하여 점좌표값
        #                                     # 도 for 문으로 함께 넘긴다.
        #                                     # 여기서 ix 의 요소가 3개가 아니면 문제가 있었던 오차가 컸던 rgb값임.3개여야함.
        #                                     # 3개이하면 문제.
        #

        # big_err_n = []
        # for nb in big_err:
        #     big_err_n.append(nb[0])
        for n, (cd, ix) in enumerate(zip(coord, rgb_large)): # 원래는 rgb 값만 넘기면 되는데 혹시나 둘다 넘기야 하는
                                                             # 상황을 대비하여 점좌표값도 for 문으로 함께 넘긴다.
                                                             # 여기서 ix 의 요소가 3개가 아니면 문제가 있었던 오차가 컸던
                                                             # rgb값임.3개여야함.(3개가 아니면 문제가 되는 이유는 코드를
                                                             # 보다가 발견한 사실로 논리적인 분석을 더해봐야 함.)
                                                             # 3개이하면 문제.

            # fcd = float(cd)
            # stl 포맷을 맞추기 위한 코드 stl에서 소수점4째짜리까지 표현, 반올림 하는 듯.
            # fcd = []
            # for c in cd:
            #     _c =float(c)
            #     fc = round(_c,4)
            #     fcd.append(fc)
            # fcd = [ c for c in cd]

            # _cd = round(fcd,4)

            ######## err test
            # err_rgb = []
            # for i in ix:
            #     _i = str(i)
            #     if _i not in rgb_atom_list:
            #         err_rgb.append(i)
            # if n == 178694:
            #     temp1 = rgb_large
            # elif n == 178695:
            #     temp2 = rgb_large
            # elif n == 178696:
            #     temp3 = rgb_large
            # len_rgb_el = len(ix)
            # if len_rgb_el > 3:
            #     coord_one = '0 0 0'
            # else:
            #     coord_one =  ' '.join(map(str,ix)) # 각각의 리스트요소로 분리되어 있는 r, g, b 각값을 "r g b" 문자열로 묶는다.
            # if len_rgb_el > 3:
            # if n == 1:
            #     temp= ix
            coord_one = ' '.join(map(str, ix))  # 각각의 리스트요소로 분리되어 있는 r, g, b 각값을 "r g b" 문자열로 묶는다.
            if n in big_err_n: # rgb 인덱스가 err난 rgb의 인덱스와 동일하면
                coord_one = "-99999" # 그 값을 -99999 처리한다는 뜻.
            color_idx_itm = color_idx_dict.items() # dict_items([('1', '100 100 100'), ('2', '100 255 100'),.. 형식

            for k, v in color_idx_itm: #k= 치아구분넘버 str, v= RGB값 str
                # if len_rgb_el > 3:
                #     W.write('-99999' + "\n")
                if coord_one == v: # 동일한 RGB값이면
                    coord_one = k # 키값인 치아구분넘버로 바꾼다.
                    W.write(coord_one + "\n")
                # elif (coord_one != v) and (len(coord_one) < 4):
                #     W.write('-99999' + "\n")
                else:
                    # if len(coord_one) > 4:
                    #     coord_one = '-99999'
                    #     W.write(coord_one + "\n")
                    pass
                    # err.append(coord_one)
                # W.write(coord_one + "\n")
    ############## ouput을 만들어진 obj파일에서 point와 cell를 개수를 추출하기위한 코드 ################################
    with open(obj_output_path, 'r')as obj:
        obj_lines = obj.readlines()
    faces_spl = faces.split(" ")
    faces_num = faces_spl[2][:-1]
    vertices_spl = vertices.split(" ")
    vertices_num = vertices_spl[2][:-1]

    #### err 를 기록으로 남기기위한 코드.########################
    with open(err_output_path , 'w')as Err:

        for err_ in big_err:
            # rgb_str = ' '.join(map(str, n_rgb[1]))
            float_rgb_str = ' '.join(map(str,rgb[err_[0]])) # err rgb의 float 형태의 값.str로 변환.
            # rgb_str = ' '.join(map(str, n_rgb[1]))
            nums = len(str(len(obj_lines))) # obj_lines 객체에서 index불러올때 전체요소의 개수의 자리수만큼 칸수가 채워져
                                            # 비워진 칸은 0으로 채워지는 형식이라 (예: 1 은 000001로 표현) 이 형식을 맞추
                                            # 기 위해 obj_lines의 전체요소수를 개수를 str로 바꾼후 바뀐str의 한글자한글자
                                            # 개수를 세면 이것이 전체요소개수의 자릿수가 구해진다.
            nums = int(str(err_[0]+ 11).zfill(nums))
            # nums = "000001"
            # nums2 = int(nums)
            # nums3 = obj_lines[int(nums)]
            nnn = err_[0] +1 + int(faces_num) + int(vertices_num) + 15 #err이 wrl의 몇벌째줄인지 찾아내는 코드
            Err.write(  float_rgb_str +  "   -->float_rgb값: " + str(file)[:-4] + ".wrl파일의 "+ str(nnn)+ "번째 줄, "
                        + obj_lines[int(nums)][2:-28]+ "   -->" + str(file)[:-4] + ".obj파일 " + str(err_[0] + 12)
                       + "번째 줄, "+ str(err_) +"\n")
            # Err.write( obj_lines[int(nums)][2:-28]+ "   " + str(file)[:-4] + ".obj파일 " + str(err_[0] + 12)
            #            + "번째 줄, "+ str(err_) + ", wrl파일의 "+ str(nnn)+ "번째 줄, " + "float_rgb값 "+ float_rgb_str +"\n")
            # # ttt ="ttt"

    derg_point = "ok" # 코드한바퀴 전체를 디버그모드로 확인할때 쓰기위한 행을 표시한다.


if __name__ == "__main__":
    big_err_range = "2" # RGB의 오차범위를 몇으로 할지를 정한다.
    obj_mode = "all_zero" # obj파일의 모든 rgb값을  0으로 통일 --> AI 인풋용 데이터용.(제주한라대 제공용)
    # obj_mode = "err_zero"  # obj파일의 모든 rgb값의 제한범위를 넘은 err만 0으로 통일 --> 테스트용으로 err가 검은색으로표현됨.
    # obj_mode = "real" # # obj파일의 모든 rgb값을 실제값 그대로 표현.
    # temp = os.getcwd()
    # ttemp = './'
    root = r'../data'  # root 폴더가 있고 그아래 wrl폴더, xyz폴더가 있음.
    obj_form_path = root + '\\obj_form.obj' # obj 파일의 기본포맷으로 이를 기초로 output obj 파일을 만든다.
    # label_num_path = root + '\\Crown_tooth_label.json' # rgb값별 식별넘버가 있음.
    label_num_path = root + '\\Crown_tooth_label.json' # rgb값별 식별넘버가 있음.
    wrl_list = os.listdir(root + "\\input_wrl\\") # 인풋데이터가 있는 경로
    for file in wrl_list:
        wrl_input_path = root + "\\input_wrl\\" + file
        obj_output_path = root + "\\output_obj\\" + str(file)[:-4] + ".obj"
        xyz_output_path = root + "\\output_xyz\\" + str(file)[:-4] +".xyz"
        err_output_path = root + "\\err\\" + str(file)[:-4] + ".err"

        wrl_to_xyz(wrl_input_path, obj_form_path ,obj_output_path, xyz_output_path, label_num_path
                   ,  file, big_err_range, obj_mode)