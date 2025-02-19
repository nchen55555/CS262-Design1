from enum import Enum

class Operations(Enum):
    # server-side operations
    SUCCESS = "00"
    FAILURE = "01"
    DELIVER_MESSAGE_NOW = "02"

    # client-side operations
    LOGIN = "10"
    CREATE_ACCOUNT = "11"
    DELETE_ACCOUNT = "12"
    LIST_ACCOUNTS = "13"
    SEND_MESSAGE = "14"
    READ_MESSAGE = "15"
    DELETE_MESSAGE = "16"

class Version(Enum): 
    WIRE_PROTOCOL = "1"
    JSON = "2"

OperationNames = {
    # server-side operations
    Operations.SUCCESS.value: "Success",
    Operations.FAILURE.value: "Failure", 
    Operations.DELIVER_MESSAGE_NOW.value: "Deliver Message Now",

    # client-side operations
    Operations.LOGIN.value: "Login",
    Operations.CREATE_ACCOUNT.value: "Create Account",
    Operations.DELETE_ACCOUNT.value: "Delete Account", 
    Operations.LIST_ACCOUNTS.value: "List Accounts",
    Operations.SEND_MESSAGE.value: "Send Message",
    Operations.READ_MESSAGE.value: "Read Message",
    Operations.DELETE_MESSAGE.value: "Delete Message"
}
