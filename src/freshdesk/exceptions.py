from enum import Enum
from enum import EnumMeta
from enum import IntEnum

from requests import HTTPError


class EnumMetaUpperGetItem(EnumMeta):
    """Allow lowercase or mixedcase lookups."""

    def __getitem__(cls, name):
        return cls._member_map_[name.upper()]


class EnumMetaContainsCode(EnumMeta):
    """Check if value is in any member's values."""

    def __contains__(cls, value):
        return value in [i.value for i in cls._member_map_.values()]


class ClientOrValidationError(HTTPError):
    description = "The request body/query string is not in the correct format. For example, the Create a ticket API requires the requester_id field to be sent as part of the request and if it is missing, this status code is returned."  # noqa: 501


class AuthenticationFailure(HTTPError):
    description = " Indicates that the Authorization header is either missing or incorrect."  # noqa: 501


class AccessDenied(HTTPError):
    description = "This indicates that the agent whose credentials were used in making this request was not authorized to perform this API call. It could be that this API call requires admin level credentials or perhaps the Freshdesk portal doesn't have the corresponding feature enabled. It could also indicate that the user has reached the maximum number of failed login attempts or that the account has reached the maximum number of agents"  # noqa: 501


class RequestedResourceNotFound(HTTPError):
    description = "This status code is returned when the request contains invalid ID/Freshdesk domain in the URL or an invalid URL itself. For example, an API call to retrieve a ticket with an invalid ID will return a HTTP 404 status code to let you know that no such ticket exists."  # noqa: 501


class MethodNotAllowed(HTTPError):
    description = "This API request used the wrong HTTP verb/method. For example an API PUT request on /api/v2/tickets endpoint will return a HTTP 405 as /api/v2/tickets allows only GET and POST requests."  # noqa: 501


class UnsupportedAcceptHeader(HTTPError):
    description = "Only application/json and */* are supported. When uploading files multipart/form-data is supported."  # noqa: 501


class InconsistentOrConflictingState(HTTPError):
    description = "The resource that is being created/updated is in an inconsistent or conflicting state. For example, if you attempt to Create a Contact with an email that is already associated with an existing user, this code will be returned."  # noqa: 501


class UnsupportedContentType(HTTPError):
    description = "Content type application/xml is not supported. Only application/json is supported."  # noqa: 501


class RateLimitExceeded(HTTPError):
    description = "The API rate limit allotted for your Freshdesk domain has been exhausted."  # noqa: 501


class UnexpectedServerError(HTTPError):
    description = "Phew!! You can't do anything more here. This indicates an error at Freshdesk's side. Please email us your API script along with the response headers. We will reach you out to you and fix this ASAP."  # noqa: 501


class HTTPErrorCode(IntEnum, metaclass=EnumMetaContainsCode):
    ClientOrValidationError = 400
    AuthenticationFailure = 401
    AccessDenied = 403
    RequestedResourceNotFound = 404
    MethodNotAllowed = 405
    UnsupportedAcceptHeader = 406
    InconsistentOrConflictingState = 409
    UnsupportedContentType = 415
    RateLimitExceeded = 429
    UnexpectedServerError = 500

    def __init__(self, value):
        self.exception = eval(self.name)
        self.description = self.exception.description
        self.code = value


class ErrorCode(Enum, metaclass=EnumMetaUpperGetItem):
    MISSING_FIELD = "A mandatory attribute is missing. For example, calling Create a Contact without the mandatory email field in the request will result in this error."  # noqa: 501
    INVALID_VALUE = "This code indicates that a request contained an incorrect or blank value, or was in an invalid format."  # noqa: 501
    DUPLICATE_VALUE = "Indicates that this value already exists. This error is applicable to fields that require unique values such as the email address in a contact or the name in a company."  # noqa: 501
    DATATYPE_MISMATCH = "Indicates that the field value doesn't match the expected data type. Entering text in a numerical field would trigger this error."  # noqa: 501
    INVALID_FIELD = "An unexpected field was part of the request. If any additional field is included in the request payload (other than what is specified in the API documentation), this error will occur."  # noqa: 501
    INVALID_JSON = "Request parameter is not a valid JSON. We recommend that you validate the JSON payload with a JSON validator before firing the API request."  # noqa: 501
    INVALID_CREDENTIALS = "Incorrect or missing API credentials. As the name suggests, it indicates that the API request was made with invalid credentials. Forgetting to apply Base64 encoding on the API key is a common cause of this error."  # noqa: 501
    ACCESS_DENIED = "Insufficient privileges to perform this action. An agent attempting to access admin APIs will result in this error."  # noqa: 501
    REQUIRE_FEATURE = "Not allowed as a specific feature has to be enabled in your Freshdesk portal for you to perform this action."  # noqa: 501
    ACCOUNT_SUSPENDED = "Account has been suspended."
    SSL_REQUIRED = "HTTPS is required in the API URL."
    READONLY_FIELD = "Read only field cannot be altered."
    INCONSISTENT_STATE = "An email should be associated with the contact before converting the contact to an agent."  # noqa: 501
    MAX_AGENTS_REACHED = (
        "The account has reached the maximum number of agents."
    )
    PASSWORD_LOCKOUT = (
        "The agent has reached the maximum number of failed login attempts."
    )
    PASSWORD_EXPIRED = "The agent's password has expired."
    NO_CONTENT_REQUIRED = "No JSON data required."
    INACCESSIBLE_FIELD = "The agent is not authorized to update this field."
    INCOMPATIBLE_FIELD = (
        "The field cannot be updated due to the current state of the record."
    )

    def __init__(self, value):
        self.code = self.name.lower()
