from enum import Enum

class Operations(Enum): 
    # server-side operations 
    SUCCESS = "00"
    FAILURE = "01" 

    # client-side operations 
    LOGIN = "10"
    CREATE_ACCOUNT = "11"
    DELETE_ACCOUNT = "12" 
    LIST_ACCOUNTS = "13"
    SEND_MESSAGE = "14" 
    READ_MESSAGE = "15"
    DELETE_MESSAGE = "16"

class OperationNames(Enum): 
    # server-side operations 
    SUCCESS = "Success"
    FAILURE = "Failure" 

    # client-side operations 
    LOGIN = "Login"
    CREATE_ACCOUNT = "Create Account"
    DELETE_ACCOUNT = "Delete Account" 
    LIST_ACCOUNTS = "List Accounts"
    SEND_MESSAGE = "Send Message" 
    READ_MESSAGE = "Read Message"
    DELETE_MESSAGE = "Delete Message"


    
