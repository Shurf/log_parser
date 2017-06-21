import difference_parser

def main():
    parser = difference_parser.DifferenceParser('7.00.27.02270')
    parser.fill_structures()
    parser.print_results()




if __name__ == '__main__':
    main()
