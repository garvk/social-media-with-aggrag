from library.aggrag.aggrag import AggRAG
# Initialize the Aggrag object with the configuration from cforge
import os, sys
import asyncio

# Get the current working directory
current_dir = os.getcwd()

async def main():
    print(f"current working dir: {current_dir}")
    cforge_file_path= os.path.join(current_dir, "configurations/Bhai Conversation__1725816673772/iteration 1/flow-1726220592988.cforge" )
    rag_object = AggRAG(cforge_file_path=cforge_file_path)
    print(f"rag object created")
    print(f"Use case: {rag_object.usecase_name}, {rag_object.iteration}")
    # Construct the path to the 'index' directory
    index_dir = os.path.join(current_dir, 'configurations', rag_object.usecase_name, rag_object.iteration, 'index')
    rag_object.ragstore.base.index_name = "base_index_1__1726221463705_1726222962860"
    rag_object.ragstore.base.PERSIST_DIR = index_dir
    # Update the PERSIST_DIR
    rag_object.PERSIST_DIR = index_dir

    await rag_object.retrieve_all_index_async()
    response = await rag_object.ragstore_chat(query="hi")
    print(response)

asyncio.run(main())
