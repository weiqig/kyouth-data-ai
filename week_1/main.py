import sys
from src import Ingestor, Processor, Loader, Profiler


def display_help(command_list: list) -> None:
    '''
    Display help and list of commands.
    '''
    print("\ncommands:\n", end='')
    print(", ".join(command_list))


def main() -> None:
    '''
    Execute the program.
    '''
    command_list = ['ingest', 'process', 'load', 'profile', 'all']

    if len(sys.argv) < 2:
        print("Usage: python main.py <command> <process_amount (optional)>")
        display_help(command_list)
        return

    source = "data/0_source"
    bronze = "data/1_bronze"
    silver = "data/2_silver"
    gold = "data/3_gold"

    try:
        ingestor = Ingestor(source, bronze)
        processor = Processor(bronze, silver)
        loader = Loader(silver, gold)
        profiler = Profiler(gold)
        command = sys.argv[1]

        match command:
            case 'ingest':
                ingestor.ingest_all_mhtml()
            case 'process':
                processor.process_all_html()
            case 'load':
                loader.load_all_jsons()
            case 'profile':
                profiler.run_data_profile()
            case 'all':
                ingestor.ingest_all_mhtml()
                processor.process_all_html()
                loader.load_all_jsons()
                profiler.run_data_profile()
            case _:
                print("Unknown command:", command)
                display_help(command_list)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
