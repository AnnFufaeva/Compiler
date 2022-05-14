from LarkParser import program


def main() -> None:
    prog5 = '''
        int input_int(string name) {
            if (name != "") {
                print("Введите " + name + ": ");
            }
            return to_int(read());

            // bool a() { }
        };
        int input_int2(string name, int a, int name2) {
            if (name != "") {
                print("Введите " + name + ": ");
            }
            return 2;
        };
        input_int2("",2,2);
    '''
    prog6 = '''
        int input_int(string name) {
            if (name != "") {
                print("Введите " + name + ": ");
            }
            int a = to_int(read());
            if (a > 0) {
                println(a);
            }
            return a;
        };
    '''
    prog7 = '''
        int[3] b = [1,2,3];
        b = [1,3,2 ];
        int d = b[0];
        //b[3] = 4;
    '''

    program.execute(prog7)


if __name__ == "__main__":
    main()